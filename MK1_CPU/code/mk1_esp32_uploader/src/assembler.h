// MK1 Assembler — runs on ESP32
//
// Two-pass assembler: pass 1 collects labels, pass 2 emits bytes.
// Supports the customasm-style syntax used by the MK1 programs:
//   - Labels: "name:" or ".name:" (local labels, scoped to last global label)
//   - Instructions with register and immediate operands
//   - Constants: "NAME = value"
//   - Data bank: #bank ".data" / #bank ".instr"
//   - Data directives: #d8, #res, #str (in data bank)
//   - Comments: ; to end of line
//   - #include directives are ignored (libraries are built-in)

#pragma once
#include <Arduino.h>
#include "isa.h"
#include "stdlib_asm.h"

static const int CODE_SIZE = 256;
static const int DATA_SIZE = 256;
static const int MAX_LABELS = 128;
static const int MAX_CONSTANTS = 32;
static const int MAX_LINES = 512;
static const int MAX_ERRORS = 16;

struct Label {
    char name[48];
    uint16_t address;
    bool is_data;  // true if in data bank
};

struct Constant {
    char name[32];
    int value;
};

struct AsmError {
    int line;
    char message[80];
};

static const int EEPROM_SIZE = 4096;  // AT24C32 = 4KB

struct AsmResult {
    uint8_t code[CODE_SIZE];
    uint8_t data[DATA_SIZE];
    uint8_t stack[DATA_SIZE];   // page 2 (stack page) overlay storage
    uint8_t page3[DATA_SIZE];
    uint8_t eeprom[EEPROM_SIZE]; // AT24C32 EEPROM data for upload
    uint8_t p3patch[DATA_SIZE]; // page3 patch: written AFTER init self-copy
    int code_size;
    int data_size;
    int stack_size;
    int page3_size;
    int eeprom_size;
    int p3patch_size;           // bytes to patch in page3 after self-copy
    int p3patch_cycles;         // clock cycles needed for init before patching
    AsmError errors[MAX_ERRORS];
    int error_count;
};

// ── Helper functions ─────────────────────────────────────────────────

static bool isWhitespace(char c) { return c == ' ' || c == '\t'; }

static void skipWs(const char*& p) {
    while (*p && isWhitespace(*p)) p++;
}

static bool startsWith(const char* str, const char* prefix) {
    while (*prefix) {
        if (tolower(*str) != tolower(*prefix)) return false;
        str++; prefix++;
    }
    return true;
}

static bool isIdentChar(char c) {
    return isalnum(c) || c == '_' || c == '$' || c == '.';
}

static int parseToken(const char* p, char* out, int maxLen) {
    int i = 0;
    while (*p && *p != ',' && isIdentChar(*p) && i < maxLen - 1) {
        out[i++] = *p++;
    }
    out[i] = 0;
    return i;
}

static void skipSep(const char*& p) {
    /* Skip whitespace and commas between operands */
    while (*p == ' ' || *p == '\t' || *p == ',') p++;
}

static int findRegister(const char* name) {
    for (int i = 0; REGISTERS[i].name; i++) {
        if (strcasecmp(name, REGISTERS[i].name) == 0) return REGISTERS[i].code;
    }
    return -1;
}

static int findAluOp(const char* name) {
    for (int i = 0; ALU_OPS[i].name; i++) {
        if (strcasecmp(name, ALU_OPS[i].name) == 0) return ALU_OPS[i].code;
    }
    return -1;
}

static int parseNumber(const char* p, bool& ok) {
    ok = false;
    skipWs(p);
    if (!*p) return 0;

    bool negative = false;
    if (*p == '-') { negative = true; p++; }

    int base = 10;
    if (p[0] == '0' && (p[1] == 'x' || p[1] == 'X')) { base = 16; p += 2; }
    else if (p[0] == '0' && (p[1] == 'b' || p[1] == 'B')) { base = 2; p += 2; }

    if (!*p || (!isdigit(*p) && !isxdigit(*p))) return 0;

    char* end;
    long val = strtol(p, &end, base);
    if (end != p) {
        ok = true;
        return negative ? -(int)val : (int)val;
    }
    return 0;
}

// ── Main assembler class ─────────────────────────────────────────────

class MK1Assembler {
public:
    AsmResult result;

    void assemble(const char* source) {
        memset(&result, 0, sizeof(result));
        labelCount = 0;
        constCount = 0;
        lastGlobalLabel[0] = 0;

        // Pass 1: collect labels and constants
        pass(source, true);
        if (result.error_count > 0) return;

        // Pass 2: emit code
        lastGlobalLabel[0] = 0;
        codeEmitTarget = 0;  // reset — pass 1 may have left this as page3
        pass(source, false);
    }

private:
    Label labels[MAX_LABELS];
    int labelCount;
    Constant constants[MAX_CONSTANTS];
    int constCount;
    char lastGlobalLabel[48];

    void addError(int line, const char* msg) {
        if (result.error_count < MAX_ERRORS) {
            result.errors[result.error_count].line = line;
            strncpy(result.errors[result.error_count].message, msg, 79);
            result.errors[result.error_count].message[79] = 0;
            result.error_count++;
        }
    }

    void addLabel(const char* name, uint16_t addr, bool is_data) {
        if (labelCount >= MAX_LABELS) return;
        // Expand local labels: ".foo" becomes "lastGlobal.foo"
        if (name[0] == '.') {
            snprintf(labels[labelCount].name, sizeof(labels[0].name),
                     "%s%s", lastGlobalLabel, name);
        } else {
            strncpy(labels[labelCount].name, name, sizeof(labels[0].name) - 1);
        }
        labels[labelCount].address = addr;
        labels[labelCount].is_data = is_data;
        labelCount++;
    }

    int findLabel(const char* name) {
        char expanded[48];
        if (name[0] == '.') {
            snprintf(expanded, sizeof(expanded), "%s%s", lastGlobalLabel, name);
        } else {
            strncpy(expanded, name, sizeof(expanded) - 1);
            expanded[sizeof(expanded) - 1] = 0;
        }
        for (int i = 0; i < labelCount; i++) {
            if (strcmp(labels[i].name, expanded) == 0) return labels[i].address;
        }
        return -1;
    }

    void addConstant(const char* name, int value) {
        if (constCount >= MAX_CONSTANTS) return;
        strncpy(constants[constCount].name, name, sizeof(constants[0].name) - 1);
        constants[constCount].value = value;
        constCount++;
    }

    int findConstant(const char* name) {
        for (int i = 0; i < constCount; i++) {
            if (strcmp(constants[i].name, name) == 0) return constants[i].value;
        }
        return -1;
    }

    // Evaluate a simple expression: supports +, -, * with integer operands/constants
    int evalExpr(const char* p, int line, bool pass1) {
        skipWs(p);
        // Parse first term
        int result = evalTerm(p, line, pass1);
        skipWs(p);
        while (*p == '+' || *p == '-') {
            char op = *p++;
            skipWs(p);
            int rhs = evalTerm(p, line, pass1);
            if (op == '+') result += rhs;
            else result -= rhs;
            skipWs(p);
        }
        return result;
    }

    int evalTerm(const char*& p, int line, bool pass1) {
        skipWs(p);
        bool neg = false;
        if (*p == '-') { neg = true; p++; skipWs(p); }

        int val = 0;
        bool ok;
        if (isdigit(*p) || (*p == '0' && (p[1] == 'x' || p[1] == 'b'))) {
            val = parseNumber(p, ok);
            // Advance past the number
            if (*p == '0' && (p[1] == 'x' || p[1] == 'X')) { p += 2; while (isxdigit(*p)) p++; }
            else if (*p == '0' && (p[1] == 'b' || p[1] == 'B')) { p += 2; while (*p == '0' || *p == '1') p++; }
            else { while (isdigit(*p)) p++; }
        } else if (isalpha(*p) || *p == '_') {
            char tok[32];
            int len = parseToken(p, tok, sizeof(tok));
            p += len;
            int c = findConstant(tok);
            if (c >= 0) val = c;
            else {
                int l = findLabel(tok);
                if (l >= 0) val = l;
            }
        } else if (*p == '(') {
            p++;
            val = evalExpr(p, line, pass1);
            if (*p == ')') p++;
        }

        skipWs(p);
        // Handle * (higher precedence)
        while (*p == '*') {
            p++; skipWs(p);
            int rhs = 0;
            if (isdigit(*p)) {
                rhs = parseNumber(p, ok);
                while (isdigit(*p)) p++;
            }
            val *= rhs;
            skipWs(p);
        }

        return neg ? -val : val;
    }

    // Resolve an operand that could be a number, label, or constant
    int resolveValue(const char* tok, int line, bool pass1) {
        // Handle simple expressions: label+N or label-N
        const char* plus = strchr(tok, '+');
        const char* minus = (plus == nullptr) ? strchr(tok, '-') : nullptr;
        if (plus || minus) {
            const char* op = plus ? plus : minus;
            char left[48]; int llen = op - tok;
            if (llen > 0 && llen < (int)sizeof(left)) {
                strncpy(left, tok, llen); left[llen] = 0;
                int lv = resolveValue(left, line, pass1);
                // Right operand: resolve as number, constant, or label
                char right[48];
                strncpy(right, op + 1, sizeof(right) - 1);
                right[sizeof(right) - 1] = 0;
                int rv = resolveValue(right, line, pass1);
                return plus ? (lv + rv) : (lv - rv);
            }
        }

        bool ok;
        int v = parseNumber(tok, ok);
        if (ok) return v;

        // Try constant
        int c = findConstant(tok);
        if (c >= 0) return c;

        // Try label
        int l = findLabel(tok);
        if (l >= 0) return l;

        if (!pass1) {
            char msg[80];
            snprintf(msg, sizeof(msg), "Undefined symbol: %.40s", tok);
            addError(line, msg);
        }
        return 0;
    }

    int codeEmitTarget = 0;  // 0 = page 0 (normal), 3 = page 3 (overlay code)
    int overlayBaseAddr = 0; // virtual base address for overlay code labels

    void emitCode(uint8_t byte, bool pass1) {
        if (codeEmitTarget == 3) {
            emitPage3(byte, pass1);
            result.code_size++;  // advance code PC for label resolution
            return;
        }
        if (codeEmitTarget == 1) {
            emitData(byte, pass1);
            result.code_size++;
            return;
        }
        if (codeEmitTarget == 2) {
            emitStack(byte, pass1);
            result.code_size++;
            return;
        }
        if (codeEmitTarget == 4) {
            emitEeprom(byte, pass1);
            result.code_size++;  // advance code PC for label resolution
            return;
        }
        if (codeEmitTarget == 5) {
            emitP3Patch(byte, pass1);
            result.code_size++;  // advance code PC for label resolution
            return;
        }
        if (!pass1 && result.code_size < CODE_SIZE)
            result.code[result.code_size] = byte;
        result.code_size++;
    }

    void emitData(uint8_t byte, bool pass1) {
        if (!pass1 && result.data_size < DATA_SIZE)
            result.data[result.data_size] = byte;
        result.data_size++;
    }

    void emitStack(uint8_t byte, bool pass1) {
        if (!pass1 && result.stack_size < DATA_SIZE)
            result.stack[result.stack_size] = byte;
        result.stack_size++;
    }

    void emitPage3(uint8_t byte, bool pass1) {
        if (!pass1 && result.page3_size < DATA_SIZE) {
            result.page3[result.page3_size] = byte;

        }
        result.page3_size++;
    }

    void emitEeprom(uint8_t byte, bool pass1) {
        if (!pass1 && result.eeprom_size < EEPROM_SIZE)
            result.eeprom[result.eeprom_size] = byte;
        result.eeprom_size++;
    }

    void emitP3Patch(uint8_t byte, bool pass1) {
        if (!pass1 && result.p3patch_size < DATA_SIZE)
            result.p3patch[result.p3patch_size] = byte;
        result.p3patch_size++;
    }

    // Emit to whichever bank is active (used for data directives)
    void emitBank(uint8_t byte, bool pass1, int bank) {
        if (bank == 4) emitEeprom(byte, pass1);
        else if (bank == 3) emitPage3(byte, pass1);
        else if (bank == 1) emitData(byte, pass1);
        else emitCode(byte, pass1);
    }

    void pass(const char* source, bool pass1, bool isInclude = false) {
        if (!pass1 && !isInclude) {
            // Fill code page with HLT (0x7F) — prevents runaway execution past program end
            memset(result.code, 0x7F, CODE_SIZE);
            result.code_size = 0;
            result.data_size = 0;
            result.stack_size = 0;
            result.page3_size = 0;
            result.eeprom_size = 0;
            result.p3patch_size = 0;
        }

        int bank = 0;  // 0=code, 1=data, 3=page3
        int lineNum = 0;

        const char* p = source;
        while (*p) {
            lineNum++;

            // Extract line
            const char* lineStart = p;
            while (*p && *p != '\n') p++;
            int lineLen = p - lineStart;
            if (*p == '\n') p++;

            char line[256];
            int len = lineLen < 255 ? lineLen : 255;
            memcpy(line, lineStart, len);
            line[len] = 0;

            // Strip comment
            char* semi = strchr(line, ';');
            if (semi) *semi = 0;

            // Trim trailing whitespace
            len = strlen(line);
            while (len > 0 && isWhitespace(line[len - 1])) line[--len] = 0;

            const char* lp = line;
            skipWs(lp);
            if (!*lp) continue;  // empty line

            // Handle "section" directive
            if (startsWith(lp, "section")) {
                if (strstr(lp, "stack_code")) {
                    // Overlay code stored in stack page: labels at code PC, bytes to stack buffer
                    bank = 0;
                    codeEmitTarget = 2;  // emit to stack page (page 2)
                } else if (strstr(lp, "data_code")) {
                    // Overlay code stored in data page: labels at code PC, bytes to data buffer
                    bank = 0;
                    codeEmitTarget = 1;
                } else if (strstr(lp, "page3_kernel")) {
                    // Kernel code stored in page 3: resets code PC to 0 for
                    // self-copy to code[0]. Labels at address 0+.
                    bank = 0;
                    codeEmitTarget = 3;
                    result.code_size = 0;   // reset PC for kernel base address
                    result.page3_size = 0;  // reset page3 write pointer too
                } else if (strstr(lp, "page3_code")) {
                    // Overlay code stored in page 3: same but emit to page 3
                    bank = 0;
                    codeEmitTarget = 3;
                } else if (strstr(lp, "p3patch")) {
                    // Page3 post-init patch: overlay data written after self-copy.
                    // Instructions and bytes go to p3patch buffer at code PC.
                    bank = 0;
                    codeEmitTarget = 5;  // emit to p3patch buffer
            } else if (strstr(lp, "eeprom")) {
                    bank = 0;  // bank=0 so instructions are parsed normally
                    codeEmitTarget = 4;  // emit assembled bytes to EEPROM buffer
                } else if (strstr(lp, "page3")) {
                    bank = 3;  // raw data in page 3
                    codeEmitTarget = 0;
                } else if (strstr(lp, "data")) {
                    bank = 1;
                    codeEmitTarget = 0;
                } else {
                    bank = 0;
                    codeEmitTarget = 0;
                }
                continue;
            }

            // Handle directives
            if (*lp == '#') {
                lp++;
                if (startsWith(lp, "include")) {
                    // Check if it's the standard library
                    if (strstr(lp, "mk1_std") || strstr(lp, "mk1std")) {
                        // Recursively assemble the embedded standard library
                        pass(MK1_STDLIB_ASM, pass1, true);
                    }
                    // Skip other includes (mk1.cpu is ISA definition, not needed)
                    continue;
                }
                if (startsWith(lp, "bank")) {
                    if (strstr(lp, "page3") || strstr(lp, ".page3")) bank = 3;
                    else if (strstr(lp, ".data")) bank = 1;
                    else bank = 0;
                    continue;
                }
                if (startsWith(lp, "d8") || startsWith(lp, "res") || startsWith(lp, "str")) {
                    // Data directives — emit to current bank
                    if (startsWith(lp, "d8")) {
                        lp += 2; skipWs(lp);
                        char tok[32];
                        parseToken(lp, tok, sizeof(tok));
                        int v = resolveValue(tok, lineNum, pass1);
                        emitBank(v & 0xFF, pass1, bank);
                    } else if (startsWith(lp, "res")) {
                        lp += 3; skipWs(lp);
                        bool ok; int count = parseNumber(lp, ok);
                        if (ok) for (int i = 0; i < count; i++) emitBank(0, pass1, bank);
                    } else if (startsWith(lp, "str")) {
                        lp += 3; skipWs(lp);
                        if (*lp == '"') {
                            lp++;
                            while (*lp && *lp != '"') {
                                if (*lp == '\\' && lp[1] == '0') {
                                    emitBank(0, pass1, bank); lp += 2;
                                } else {
                                    emitBank(*lp, pass1, bank); lp++;
                                }
                            }
                        }
                    }
                    continue;
                }
                continue;  // unknown directive
            }

            // Handle vasm-style data directives (without # prefix)
            if (startsWith(lp, "byte ") || startsWith(lp, "byte\t")) {
                lp += 4; skipWs(lp);
                // Read full expression (including +/-) not just an ident token
                char tok[48]; int ti = 0;
                while (*lp && *lp != ',' && *lp != ' ' && *lp != '\t' && *lp != ';' && ti < 47)
                    tok[ti++] = *lp++;
                tok[ti] = 0;
                int v = resolveValue(tok, lineNum, pass1);
                // Use emitCode when codeEmitTarget is active (page3_code, data_code,
                // stack_code, eeprom sections). Otherwise use bank-based emit.
                if (codeEmitTarget != 0)
                    emitCode(v & 0xFF, pass1);
                else
                    emitBank(v & 0xFF, pass1, bank);
                continue;
            }
            if (startsWith(lp, "ds ") || startsWith(lp, "ds\t")) {
                lp += 2; skipWs(lp);
                bool ok; int count = parseNumber(lp, ok);
                if (ok) for (int j = 0; j < count; j++) emitBank(0, pass1, bank);
                continue;
            }
            if (startsWith(lp, "org ") || startsWith(lp, "org\t")) {
                // .org N: set code PC to address N. Pads with HLT if advancing.
                const char* p = lp + 4;
                skipWs(p);
                char tok[32]; parseToken(p, tok, sizeof(tok));
                int target = resolveValue(tok, lineNum, pass1);
                int current = result.code_size;
                if (target > current) {
                    // Forward: pad with HLT
                    while (result.code_size < target) {
                        emitCode(0x7F, pass1);
                    }
                } else {
                    // Backward or same: just set PC (for overlay code that follows resident)
                    result.code_size = target;
                }
                continue;
            }

            // Check for constant definition: NAME = expr
            {
                const char* eq = strchr(lp, '=');
                if (eq && *(eq-1) != '<' && *(eq-1) != '>' && *(eq-1) != '!') {
                    // Check it's not == or inside a label definition
                    if (*(eq+1) != '=') {
                        const char* colon = strchr(lp, ':');
                        if (!colon || eq < colon) {
                            char name[32];
                            const char* np = lp;
                            int ni = 0;
                            while (np < eq && ni < 31) {
                                if (!isWhitespace(*np)) name[ni++] = *np;
                                np++;
                            }
                            name[ni] = 0;
                            const char* vp = eq + 1;
                            skipWs(vp);
                            int val = evalExpr(vp, lineNum, pass1);
                            if (pass1) addConstant(name, val);
                            continue;
                        }
                    }
                }
            }

            // Check for label: "name:" at start of line
            {
                const char* colon = strchr(lp, ':');
                if (colon) {
                    char labelName[48];
                    int li = 0;
                    const char* lp2 = lp;
                    while (lp2 < colon && li < 47) {
                        if (!isWhitespace(*lp2)) labelName[li++] = *lp2;
                        lp2++;
                    }
                    labelName[li] = 0;

                    uint16_t addr = (bank == 1) ? result.data_size :
                                    (bank == 3) ? result.page3_size : result.code_size;
                    if (pass1) addLabel(labelName, addr, bank != 0);
                    if (labelName[0] != '.') {
                        strncpy(lastGlobalLabel, labelName, sizeof(lastGlobalLabel) - 1);
                    }

                    lp = colon + 1;
                    skipWs(lp);
                    if (!*lp) continue;  // label-only line
                }
            }

            // Parse instruction
            if (bank != 0) {
                // In data/page3 bank — handle directives after labels and bare data
                if (*lp == '#') {
                    const char* dp = lp + 1;
                    if (startsWith(dp, "d8")) {
                        dp += 2; skipWs(dp);
                        char tok[32]; parseToken(dp, tok, sizeof(tok));
                        int v = resolveValue(tok, lineNum, pass1);
                        emitBank(v & 0xFF, pass1, bank);
                    } else if (startsWith(dp, "res")) {
                        dp += 3; skipWs(dp);
                        bool ok; int count = parseNumber(dp, ok);
                        if (ok) for (int i = 0; i < count; i++) emitBank(0, pass1, bank);
                    } else if (startsWith(dp, "str")) {
                        dp += 3; skipWs(dp);
                        if (*dp == '"') {
                            dp++;
                            while (*dp && *dp != '"') {
                                if (*dp == '\\' && dp[1] == '0') { emitBank(0, pass1, bank); dp += 2; }
                                else { emitBank(*dp, pass1, bank); dp++; }
                            }
                        }
                    }
                    continue;
                }
                char tok[32];
                parseToken(lp, tok, sizeof(tok));
                int v = resolveValue(tok, lineNum, pass1);
                emitBank(v & 0xFF, pass1, bank);
                continue;
            }

            parseInstruction(lp, lineNum, pass1);
        }
    }

    void parseInstruction(const char* lp, int lineNum, bool pass1) {
        char mnemonic[16];
        int mlen = parseToken(lp, mnemonic, sizeof(mnemonic));
        if (mlen == 0) return;
        const char* afterMnem = lp + mlen;  // pointer into SOURCE after mnemonic
        skipWs(afterMnem);

        // Build extended mnemonic for multi-word fixed instructions (exr, exw)
        // Try progressively longer matches
        char extMnem[32];
        strncpy(extMnem, mnemonic, sizeof(extMnem) - 1);
        extMnem[sizeof(extMnem) - 1] = 0;
        const char* afterExt = afterMnem;  // tracks position after extended mnemonic

        // ── Check fixed instructions (longest match first) ──
        for (int pass = 0; pass < 3; pass++) {
            for (int i = 0; FIXED_INSTRUCTIONS[i].mnemonic; i++) {
                if (strcasecmp(extMnem, FIXED_INSTRUCTIONS[i].mnemonic) == 0) {
                    emitCode(FIXED_INSTRUCTIONS[i].opcode, pass1);
                    InstrArgs ak = FIXED_INSTRUCTIONS[i].args;
                    int nImm = (ak == ARGS_IMM) ? 1 :
                               (ak == ARGS_IMM2) ? 2 :
                               (ak == ARGS_IMM3) ? 3 : 0;
                    const char* tp = afterExt;
                    for (int k = 0; k < nImm; k++) {
                        skipWs(tp);
                        char tok[32];
                        int n = parseToken(tp, tok, sizeof(tok));
                        tp += n;
                        // Skip separator (comma or space) between operands.
                        while (*tp == ',' || *tp == ' ' || *tp == '\t') tp++;
                        int v = resolveValue(tok, lineNum, pass1);
                        emitCode(v & 0xFF, pass1);
                    }
                    return;
                }
            }
            // Try extending mnemonic with next token
            if (*afterExt && pass < 2) {
                char nextTok[16];
                int nlen = parseToken(afterExt, nextTok, sizeof(nextTok));
                if (nlen > 0) {
                    int elen = strlen(extMnem);
                    extMnem[elen] = ' ';
                    strncpy(extMnem + elen + 1, nextTok, sizeof(extMnem) - elen - 2);
                    afterExt += nlen;
                    skipWs(afterExt);
                } else break;
            } else break;
        }

        // ── "out" with register or immediate ──
        if (strcasecmp(mnemonic, "out") == 0) {
            const char* ap = afterMnem;
            if (!*ap) {
                emitCode(0x06, pass1);  // out = mov $a, $out
                return;
            }
            char tok[32];
            parseToken(ap, tok, sizeof(tok));
            int reg = findRegister(tok);
            if (reg >= 0) {
                emitCode((0b00 << 6) | (reg << 3) | 6, pass1);  // mov reg, $out
                return;
            }
            // Immediate
            int v = resolveValue(tok, lineNum, pass1);
            emitCode(0x3E, pass1);  // mov imm, $out = 00_111_110
            emitCode(v & 0xFF, pass1);
            return;
        }

        const char* args = afterMnem;

        // ── "cmp" ──
        if (strcasecmp(mnemonic, "cmp") == 0) {
            char tok[32];
            parseToken(args, tok, sizeof(tok));
            for (int i = 0; i < 4; i++) {
                if (CMP_VARIANTS[i].operand && strcasecmp(tok, CMP_VARIANTS[i].operand) == 0) {
                    emitCode(CMP_VARIANTS[i].opcode, pass1);
                    return;
                }
            }
            // Immediate form: use cmpi opcode (doesn't clobber B)
            {
                int v = resolveValue(tok, lineNum, pass1);
                emitCode(0xFD, pass1);         // cmpi N
                emitCode(v & 0xFF, pass1);
                return;
            }
        }

        // ── "push" / "pop" ──
        if (strcasecmp(mnemonic, "push") == 0) {
            char tok[32];
            parseToken(args, tok, sizeof(tok));
            int reg = findRegister(tok);
            if (reg >= 0 && reg < 6) {
                emitCode((0b10 << 6) | (reg << 3) | 4, pass1);  // stor reg, [$sp]
                return;
            }
            addError(lineNum, "push: invalid register");
            return;
        }
        if (strcasecmp(mnemonic, "pop") == 0) {
            char tok[32];
            parseToken(args, tok, sizeof(tok));
            int reg = findRegister(tok);
            if (reg >= 0 && reg < 7) {
                emitCode((0b01 << 6) | (reg << 3) | 4, pass1);  // load reg, [$sp]
                return;
            }
            addError(lineNum, "pop: invalid register");
            return;
        }

        // ── "mov" — register to register ──
        if (strcasecmp(mnemonic, "mov") == 0) {
            char tok1[32], tok2[32];
            int n1 = parseToken(args, tok1, sizeof(tok1));
            args += n1; skipSep(args);
            parseToken(args, tok2, sizeof(tok2));
            int src = findRegister(tok1);
            int dst = findRegister(tok2);
            if (src >= 0 && dst >= 0) {
                emitCode((0b00 << 6) | (src << 3) | dst, pass1);
                return;
            }
            addError(lineNum, "mov: expected two registers");
            return;
        }

        // ── "ldi" — load immediate ──
        if (strcasecmp(mnemonic, "ldi") == 0) {
            char tok1[32], tok2[32];
            int n1 = parseToken(args, tok1, sizeof(tok1));
            args += n1; skipSep(args);
            parseToken(args, tok2, sizeof(tok2));
            int reg = findRegister(tok1);
            if (reg >= 0) {
                emitCode((0b00 << 6) | (7 << 3) | reg, pass1);  // mov imm, reg
                int v = resolveValue(tok2, lineNum, pass1);
                emitCode(v & 0xFF, pass1);
                return;
            }
            addError(lineNum, "ldi: expected register and value");
            return;
        }

        // ── "ld" — load from memory ──
        if (strcasecmp(mnemonic, "ld") == 0) {
            char tok1[32], tok2[32];
            int n1 = parseToken(args, tok1, sizeof(tok1));
            args += n1; skipSep(args);

            int dst = findRegister(tok1);
            if (dst < 0) { addError(lineNum, "ld: expected destination register"); return; }

            // Check for [reg] syntax
            if (*args == '[') {
                args++; skipWs(args);
                parseToken(args, tok2, sizeof(tok2));
                int addr_reg = findRegister(tok2);
                if (addr_reg >= 0) {
                    emitCode((0b01 << 6) | (dst << 3) | addr_reg, pass1);
                    return;
                }
            }
            // Immediate address
            parseToken(args, tok2, sizeof(tok2));
            int v = resolveValue(tok2, lineNum, pass1);
            emitCode((0b01 << 6) | (dst << 3) | 7, pass1);
            emitCode(v & 0xFF, pass1);
            return;
        }

        // ── "st" — store to memory ──
        if (strcasecmp(mnemonic, "st") == 0) {
            char tok1[32], tok2[32];
            int n1 = parseToken(args, tok1, sizeof(tok1));
            args += n1; skipSep(args);

            int src = findRegister(tok1);
            if (src < 0) { addError(lineNum, "st: expected source register"); return; }

            if (*args == '[') {
                args++; skipWs(args);
                parseToken(args, tok2, sizeof(tok2));
                int addr_reg = findRegister(tok2);
                if (addr_reg >= 0) {
                    emitCode((0b10 << 6) | (src << 3) | addr_reg, pass1);
                    return;
                }
            }
            parseToken(args, tok2, sizeof(tok2));
            int v = resolveValue(tok2, lineNum, pass1);
            emitCode((0b10 << 6) | (src << 3) | 7, pass1);
            emitCode(v & 0xFF, pass1);
            return;
        }

        // ── ALU immediate: "addi", "subi", "ori", "andi" ──
        {
            int alen = strlen(mnemonic);
            if (alen >= 3 && mnemonic[alen - 1] == 'i') {
                char base[16];
                strncpy(base, mnemonic, alen - 1);
                base[alen - 1] = 0;
                int op = findAluOp(base);
                if (op >= 0) {
                    char tok1[32], tok2[32];
                    int n1 = parseToken(args, tok1, sizeof(tok1));
                    args += n1; skipSep(args);
                    parseToken(args, tok2, sizeof(tok2));
                    int imm = resolveValue(tok1, lineNum, pass1);
                    int dst = findRegister(tok2);
                    if (dst >= 0 && dst < 4) {
                        emitCode((0b1011 << 4) | (op << 2) | dst, pass1);
                        emitCode(imm & 0xFF, pass1);
                        return;
                    }
                    addError(lineNum, "ALU immediate: invalid destination (must be $a-$d)");
                    return;
                }
            }
        }

        // ── ALU register: "add", "sub", "or", "and" ──
        {
            int op = findAluOp(mnemonic);
            if (op >= 0) {
                char tok1[32], tok2[32];
                int n1 = parseToken(args, tok1, sizeof(tok1));
                args += n1; skipSep(args);
                parseToken(args, tok2, sizeof(tok2));
                int rs = findRegister(tok1);
                int rd = findRegister(tok2);
                if (rs >= 0 && rs < 4 && rd >= 0 && rd < 4) {
                    uint8_t opc = (0b11 << 6) | (op << 4) | (rs << 2) | rd;
                    // Check for reclaimed opcodes that are now special instructions
                    static const uint8_t reclaimed[] = {0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,
                        // Register inc/dec (decc/decb/incc/incd/incb/decd)
                        0xD8,0xDC,0xE8,0xEC,0xF5,0xFC,
                        0xD1,0xD2,0xD3,0xD5,0xD7,0xD9,0xDA,0xDB,0xDD,0xDE,0xDF,
                        0xE1,0xE2,0xE3,0xE6,0xE7,0xE9,0xED,0xF0,0xF1,0xF2,0xF3,0xF7,0xFD,0xFF,0};
                    bool collision = false;
                    for (int i = 0; reclaimed[i]; i++) {
                        if (opc == reclaimed[i]) { collision = true; break; }
                    }
                    if (collision) {
                        addError(lineNum, "ALU combo reclaimed for special instruction");
                        return;
                    }
                    emitCode(opc, pass1);
                    return;
                }
                addError(lineNum, "ALU: operands must be $a-$d");
                return;
            }
        }

        // ── Unknown instruction ──
        char msg[80];
        snprintf(msg, sizeof(msg), "Unknown instruction: %.40s", mnemonic);
        addError(lineNum, msg);
    }
};
