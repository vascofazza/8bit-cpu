EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 11 16
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L MCU_Module:Arduino_Nano_v2.x A1
U 1 1 668C6D9C
P 6050 3650
F 0 "A1" H 6050 2561 50  0000 C CNN
F 1 "Arduino Nano" H 6050 2470 50  0000 C CNN
F 2 "Module:Arduino_Nano" H 6050 3650 50  0001 C CIN
F 3 "https://www.arduino.cc/en/uploads/Main/ArduinoNanoManual23.pdf" H 6050 3650 50  0001 C CNN
	1    6050 3650
	1    0    0    -1  
$EndComp
$Comp
L power:GND #PWR076
U 1 1 668C95BA
P 6150 5000
F 0 "#PWR076" H 6150 4750 50  0001 C CNN
F 1 "GND" H 6155 4827 50  0000 C CNN
F 2 "" H 6150 5000 50  0001 C CNN
F 3 "" H 6150 5000 50  0001 C CNN
	1    6150 5000
	1    0    0    -1  
$EndComp
$Comp
L power:VCC #PWR077
U 1 1 668C9A0D
P 6250 2250
F 0 "#PWR077" H 6250 2100 50  0001 C CNN
F 1 "VCC" H 6267 2423 50  0000 C CNN
F 2 "" H 6250 2250 50  0001 C CNN
F 3 "" H 6250 2250 50  0001 C CNN
	1    6250 2250
	1    0    0    -1  
$EndComp
Wire Wire Line
	6150 5000 6150 4700
Text HLabel 2150 3250 0    60   Output ~ 0
BUS_0
Text HLabel 2150 3350 0    60   Output ~ 0
BUS_1
Text HLabel 2150 3450 0    60   Output ~ 0
BUS_2
Text HLabel 2150 3550 0    60   Output ~ 0
BUS_3
Text HLabel 2150 3650 0    60   Output ~ 0
BUS_4
Text HLabel 2150 3750 0    60   Output ~ 0
BUS_5
Text HLabel 2150 3850 0    60   Output ~ 0
BUS_6
Text HLabel 2150 3950 0    60   Output ~ 0
BUS_7
Wire Wire Line
	3650 3250 5550 3250
Wire Wire Line
	3650 3350 5550 3350
Wire Wire Line
	3650 3450 5550 3450
Wire Wire Line
	3650 3550 5550 3550
Wire Wire Line
	3650 3650 5550 3650
Wire Wire Line
	3650 3750 5550 3750
Wire Wire Line
	3650 3850 5550 3850
Wire Wire Line
	3650 3950 5550 3950
NoConn ~ 5550 3050
NoConn ~ 5550 3150
Wire Wire Line
	6050 4650 6050 4700
Wire Wire Line
	6050 4700 6150 4700
Connection ~ 6150 4700
Wire Wire Line
	6150 4700 6150 4650
NoConn ~ 6550 3450
NoConn ~ 6550 3150
NoConn ~ 6550 3050
NoConn ~ 6550 4350
NoConn ~ 6550 4250
NoConn ~ 6550 4150
NoConn ~ 6550 4050
NoConn ~ 6550 3950
Text HLabel 2800 4850 0    60   Output ~ 0
MI
Text HLabel 2800 5900 0    60   Output ~ 0
RI
Wire Wire Line
	5550 4250 5450 4250
Text HLabel 2800 5400 0    60   Output ~ 0
HL
NoConn ~ 6150 2650
$Comp
L 8bit-computer-rescue:74HCT245 U59
U 1 1 6828F39C
P 2950 3750
F 0 "U59" H 2950 4516 50  0000 C CNN
F 1 "74HCT245" H 2950 4425 50  0000 C CNN
F 2 "Package_DIP:DIP-20_W7.62mm" H 2950 3750 50  0001 C CNN
F 3 "" H 2950 3750 50  0001 C CNN
	1    2950 3750
	-1   0    0    -1  
$EndComp
$Comp
L 8bit-computer-rescue:74HCT04 U4
U 6 1 68295FCC
P 4550 4250
F 0 "U4" H 4550 4565 50  0000 C CNN
F 1 "74HCT04" H 4550 4474 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 4550 4250 50  0001 C CNN
F 3 "" H 4550 4250 50  0001 C CNN
	6    4550 4250
	-1   0    0    -1  
$EndComp
Wire Wire Line
	2150 3250 2250 3250
Wire Wire Line
	2150 3350 2250 3350
Wire Wire Line
	2150 3450 2250 3450
Wire Wire Line
	2150 3550 2250 3550
Wire Wire Line
	2150 3650 2250 3650
Wire Wire Line
	2150 3750 2250 3750
Wire Wire Line
	2150 3850 2250 3850
Wire Wire Line
	2150 3950 2250 3950
Wire Wire Line
	3650 4150 3750 4150
Wire Wire Line
	6250 2350 6250 2250
Wire Wire Line
	5450 4250 5450 5900
Wire Wire Line
	5350 4150 5350 5400
Wire Wire Line
	5350 4150 5550 4150
Wire Wire Line
	5250 4050 5250 4850
Wire Wire Line
	5250 4050 5550 4050
Wire Wire Line
	5000 4250 5100 4250
Wire Wire Line
	5100 4250 5100 4350
Wire Wire Line
	5100 4350 5150 4350
Wire Wire Line
	4100 4250 3650 4250
Connection ~ 5350 5400
Connection ~ 5250 4850
NoConn ~ 6250 2650
Connection ~ 5150 4350
Wire Wire Line
	5150 4350 5550 4350
Wire Wire Line
	2800 4850 5250 4850
Wire Wire Line
	2800 5400 5350 5400
Wire Wire Line
	2800 5900 5450 5900
Text HLabel 2800 5100 0    60   Output ~ 0
CLR
Text HLabel 2800 5650 0    60   Output ~ 0
CU_DIS
Text HLabel 2800 6150 0    60   Output ~ 0
CLK_OUT
Wire Wire Line
	2800 5100 5900 5100
Wire Wire Line
	5900 5100 5900 5400
Wire Wire Line
	5900 5400 6150 5400
Wire Wire Line
	6750 3750 6550 3750
Wire Wire Line
	6750 3750 6750 5400
Wire Wire Line
	2800 6150 5050 6150
Wire Wire Line
	5050 6150 5050 5700
Wire Wire Line
	5050 5700 6050 5700
Wire Wire Line
	6500 4700 6850 4700
Wire Wire Line
	6850 4700 6850 3650
Wire Wire Line
	6850 3650 6550 3650
Wire Wire Line
	6500 4700 6500 5700
Wire Wire Line
	2800 5650 6250 5650
Wire Wire Line
	7000 3850 6550 3850
Wire Wire Line
	7000 3850 7000 5650
Connection ~ 5450 5900
$Comp
L power:GND #PWR?
U 1 1 75F67E5B
P 6350 7100
AR Path="/5B53F237/75F67E5B" Ref="#PWR?"  Part="1" 
AR Path="/617DFBA6/75F67E5B" Ref="#PWR078"  Part="1" 
F 0 "#PWR078" H 6350 6850 50  0001 C CNN
F 1 "GND" H 6350 6950 50  0000 C CNN
F 2 "" H 6350 7100 50  0001 C CNN
F 3 "" H 6350 7100 50  0001 C CNN
	1    6350 7100
	1    0    0    -1  
$EndComp
$Comp
L Device:R_Network08 RN?
U 1 1 75F67E61
P 5950 6900
AR Path="/5B53F237/75F67E61" Ref="RN?"  Part="1" 
AR Path="/617DFBA6/75F67E61" Ref="RN10"  Part="1" 
F 0 "RN10" H 5470 6854 50  0000 R CNN
F 1 "1K" H 5470 6945 50  0000 R CNN
F 2 "Resistor_THT:R_Array_SIP9" V 6425 6900 50  0001 C CNN
F 3 "http://www.vishay.com/docs/31509/csc.pdf" H 5950 6900 50  0001 C CNN
	1    5950 6900
	-1   0    0    1   
$EndComp
Wire Wire Line
	5450 5900 5450 6700
Wire Wire Line
	5450 6700 5650 6700
Wire Wire Line
	5350 5400 5350 6600
Wire Wire Line
	5350 6600 5750 6600
Wire Wire Line
	5750 6600 5750 6700
Wire Wire Line
	5250 6550 5850 6550
Wire Wire Line
	5850 6550 5850 6700
Wire Wire Line
	5150 6500 5950 6500
Wire Wire Line
	5950 6500 5950 6700
Wire Wire Line
	5250 4850 5250 6550
Wire Wire Line
	5150 4350 5150 6500
Wire Wire Line
	6050 5700 6050 6700
Connection ~ 6050 5700
Wire Wire Line
	6050 5700 6500 5700
Wire Wire Line
	6150 5400 6150 6700
Connection ~ 6150 5400
Wire Wire Line
	6150 5400 6750 5400
Wire Wire Line
	6250 5650 6250 6700
Connection ~ 6250 5650
Wire Wire Line
	6250 5650 7000 5650
NoConn ~ 6350 6700
$Comp
L Jumper:SolderJumper_2_Bridged JP3
U 1 1 5EF7019F
P 5950 2500
F 0 "JP3" V 5996 2412 50  0000 R CNN
F 1 "Arduino_VIN" V 5905 2412 50  0000 R CNN
F 2 "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm" H 5950 2500 50  0001 C CNN
F 3 "~" H 5950 2500 50  0001 C CNN
	1    5950 2500
	0    -1   -1   0   
$EndComp
Wire Wire Line
	3750 2350 3750 4150
Connection ~ 5950 2350
Wire Wire Line
	5950 2350 6250 2350
Wire Wire Line
	3750 2350 5950 2350
$EndSCHEMATC
