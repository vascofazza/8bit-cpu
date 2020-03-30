EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
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
L MCU_Microchip_ATmega:ATmega328-PU U1
U 1 1 5F124789
P 2250 3750
F 0 "U1" H 1606 3796 50  0000 R CNN
F 1 "ATmega328-PU" H 1606 3705 50  0000 R CNN
F 2 "Package_DIP:DIP-28_W7.62mm_Socket" H 2250 3750 50  0001 C CIN
F 3 "http://ww1.microchip.com/downloads/en/DeviceDoc/ATmega328_P%20AVR%20MCU%20with%20picoPower%20Technology%20Data%20Sheet%2040001984A.pdf" H 2250 3750 50  0001 C CNN
	1    2250 3750
	1    0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_02x07_Odd_Even J1
U 1 1 5F127CDA
P 4750 3850
F 0 "J1" H 4800 4367 50  0000 C CNN
F 1 "Display" H 4800 4276 50  0000 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x07_P2.54mm_Vertical" H 4750 3850 50  0001 C CNN
F 3 "~" H 4750 3850 50  0001 C CNN
	1    4750 3850
	1    0    0    -1  
$EndComp
Text Notes 4400 3550 0    50   ~ 0
VCC
Wire Wire Line
	4550 3550 4350 3550
$Comp
L power:VCC #PWR02
U 1 1 5F128938
P 4350 2150
F 0 "#PWR02" H 4350 2000 50  0001 C CNN
F 1 "VCC" H 4367 2323 50  0000 C CNN
F 2 "" H 4350 2150 50  0001 C CNN
F 3 "" H 4350 2150 50  0001 C CNN
	1    4350 2150
	1    0    0    -1  
$EndComp
$Comp
L power:GND #PWR01
U 1 1 5F129083
P 4300 5450
F 0 "#PWR01" H 4300 5200 50  0001 C CNN
F 1 "GND" H 4305 5277 50  0000 C CNN
F 2 "" H 4300 5450 50  0001 C CNN
F 3 "" H 4300 5450 50  0001 C CNN
	1    4300 5450
	1    0    0    -1  
$EndComp
Wire Wire Line
	4300 5250 4300 5450
Wire Wire Line
	4300 5250 4450 5250
Wire Wire Line
	5700 5250 5700 3550
Wire Wire Line
	5700 3550 5400 3550
Connection ~ 4300 5250
Wire Wire Line
	4550 3750 4300 3750
Wire Wire Line
	4300 3750 4300 3400
Wire Wire Line
	4300 3400 5100 3400
Wire Wire Line
	5100 3400 5100 3550
Connection ~ 5100 3550
Wire Wire Line
	5100 3550 5050 3550
Wire Wire Line
	5050 3650 5200 3650
Wire Wire Line
	2850 2950 5200 2950
Wire Wire Line
	5200 2950 5200 3650
Text Notes 5050 3550 0    50   ~ 0
GND
Text Notes 4450 3650 0    50   ~ 0
V0
Text Notes 5050 3650 0    50   ~ 0
RS
Text Notes 4450 3750 0    50   ~ 0
R/W
Text Notes 5050 3750 0    50   ~ 0
E
Text Notes 4450 3850 0    50   ~ 0
DB0
Text Notes 5000 3850 0    50   ~ 0
DB1
Text Notes 4450 3950 0    50   ~ 0
DB2
Text Notes 5000 3950 0    50   ~ 0
DB3
Text Notes 4450 4050 0    50   ~ 0
DB4
Text Notes 5000 4050 0    50   ~ 0
DB5
Text Notes 4450 4150 0    50   ~ 0
DB6
Text Notes 5000 4150 0    50   ~ 0
DB7
Wire Wire Line
	4550 3650 4150 3650
Connection ~ 4450 5250
Wire Wire Line
	4450 5250 4900 5250
Wire Wire Line
	4350 4700 4450 4700
Wire Wire Line
	4450 4700 4450 5250
Wire Wire Line
	3950 4700 3750 4700
Wire Wire Line
	3750 4700 3750 4900
Text Notes 2900 2950 0    50   ~ 0
D12
Wire Wire Line
	2850 2850 5250 2850
Wire Wire Line
	5250 2850 5250 3750
Wire Wire Line
	5250 3750 5050 3750
Text Notes 2900 2850 0    50   ~ 0
D11
Text Notes 2900 4750 0    50   ~ 0
D5
Wire Wire Line
	2850 4750 3150 4750
Wire Wire Line
	3150 4750 3150 4050
Wire Wire Line
	3150 4050 4550 4050
Wire Wire Line
	2850 4650 3200 4650
Wire Wire Line
	3200 4650 3200 4350
Wire Wire Line
	5350 4350 5350 4050
Wire Wire Line
	5350 4050 5050 4050
Wire Wire Line
	2850 4550 4050 4550
Wire Wire Line
	4050 4550 4050 4150
Wire Wire Line
	4050 4150 4550 4150
Wire Wire Line
	2850 4450 5150 4450
Wire Wire Line
	5150 4450 5150 4150
Wire Wire Line
	5150 4150 5050 4150
NoConn ~ 4550 3850
NoConn ~ 4550 3950
NoConn ~ 5050 3850
NoConn ~ 5050 3950
Text Notes 2900 4450 0    50   ~ 0
D2
Text Notes 2900 4550 0    50   ~ 0
D3
Text Notes 2900 4650 0    50   ~ 0
D4
Wire Wire Line
	2250 2250 2250 2150
Wire Wire Line
	2250 2150 2350 2150
Connection ~ 4350 2150
Wire Wire Line
	2350 2250 2350 2150
Connection ~ 2350 2150
Wire Wire Line
	2350 2150 3400 2150
$Comp
L Device:C C1
U 1 1 5F13E223
P 5400 2400
F 0 "C1" H 5515 2446 50  0000 L CNN
F 1 "1uf" H 5515 2355 50  0000 L CNN
F 2 "Capacitor_THT:C_Disc_D4.3mm_W1.9mm_P5.00mm" H 5438 2250 50  0001 C CNN
F 3 "~" H 5400 2400 50  0001 C CNN
	1    5400 2400
	1    0    0    -1  
$EndComp
Wire Wire Line
	5400 2250 4350 2250
Wire Wire Line
	4350 2150 4350 2250
Connection ~ 4350 2250
Wire Wire Line
	4350 2250 4350 3550
Wire Wire Line
	5400 2550 5400 3500
Connection ~ 5400 3550
Wire Wire Line
	5400 3550 5100 3550
$Comp
L Connector_Generic:Conn_01x05 J2
U 1 1 5E7F213E
P 5100 4850
F 0 "J2" H 5180 4892 50  0000 L CNN
F 1 "Prog" H 5180 4801 50  0000 L CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_1x05_P2.54mm_Vertical" H 5100 4850 50  0001 C CNN
F 3 "~" H 5100 4850 50  0001 C CNN
	1    5100 4850
	1    0    0    -1  
$EndComp
Wire Wire Line
	3200 4350 5350 4350
Wire Wire Line
	2850 4350 3100 4350
Wire Wire Line
	3100 4350 3100 4300
Wire Wire Line
	3100 4300 4850 4300
Wire Wire Line
	4850 4300 4850 4650
Wire Wire Line
	4850 4650 4900 4650
Wire Wire Line
	4900 4750 4750 4750
Wire Wire Line
	4750 4750 4750 4250
Wire Wire Line
	4750 4250 2850 4250
Text Notes 4900 4650 0    50   ~ 0
TX
Text Notes 4900 4750 0    50   ~ 0
RX
Text Notes 4900 4850 0    50   ~ 0
RST
Text Notes 4900 4950 0    50   ~ 0
VCC
Text Notes 4900 5050 0    50   ~ 0
GND
Wire Wire Line
	4900 4850 4600 4850
Wire Wire Line
	4600 4850 4600 4200
Wire Wire Line
	4600 4200 3000 4200
Wire Wire Line
	3000 4200 3000 4050
Wire Wire Line
	3000 4050 2850 4050
Wire Wire Line
	4900 5050 4900 5250
Connection ~ 4900 5250
Wire Wire Line
	4900 5250 5700 5250
Wire Wire Line
	4900 4950 4800 4950
Wire Wire Line
	4800 4950 4800 4500
Wire Wire Line
	4800 4500 4250 4500
Wire Wire Line
	4250 4500 4250 3550
Wire Wire Line
	4250 3550 4350 3550
Connection ~ 4350 3550
$Comp
L Connector_Generic:Conn_02x09_Odd_Even J3
U 1 1 5E7FC93C
P 6500 3100
F 0 "J3" H 6550 3717 50  0000 C CNN
F 1 "EXT BUS" H 6550 3626 50  0000 C CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_2x09_P2.54mm_Vertical" H 6500 3100 50  0001 C CNN
F 3 "~" H 6500 3100 50  0001 C CNN
	1    6500 3100
	1    0    0    -1  
$EndComp
Wire Wire Line
	6300 3500 5900 3500
Connection ~ 5400 3500
Wire Wire Line
	5400 3500 5400 3550
Wire Wire Line
	6800 3500 7400 3500
Wire Wire Line
	7400 3500 7400 2150
Wire Wire Line
	7400 2150 4350 2150
Text Notes 6200 3500 0    50   ~ 0
GND
Text Notes 6850 3500 0    50   ~ 0
VCC
Text Notes 6850 3400 0    50   ~ 0
7
Text Notes 6850 3300 0    50   ~ 0
6
Text Notes 6850 3200 0    50   ~ 0
5
Text Notes 6850 3100 0    50   ~ 0
4
Text Notes 6850 3000 0    50   ~ 0
3
Text Notes 6850 2900 0    50   ~ 0
2
Text Notes 6850 2800 0    50   ~ 0
1
Text Notes 6850 2700 0    50   ~ 0
0
Text Notes 6100 2700 0    50   ~ 0
IRQ0
Text Notes 6100 2800 0    50   ~ 0
IRQ1
Text Notes 6100 2900 0    50   ~ 0
EN0
Text Notes 6100 3000 0    50   ~ 0
EN1
Text Notes 6100 3100 0    50   ~ 0
SIG0
Text Notes 6100 3200 0    50   ~ 0
SIG1
Text Notes 6100 3300 0    50   ~ 0
CLR
Text Notes 6100 3400 0    50   ~ 0
CLK
Wire Wire Line
	6800 2700 7000 2700
Wire Wire Line
	7000 2700 7000 1900
Wire Wire Line
	7000 1900 4050 1900
Wire Wire Line
	4050 1900 4050 3450
Wire Wire Line
	4050 3450 2850 3450
Wire Wire Line
	2850 3550 4000 3550
Wire Wire Line
	4000 3550 4000 1850
Wire Wire Line
	7050 1850 7050 2800
Wire Wire Line
	7050 2800 6800 2800
Wire Wire Line
	4000 1850 7050 1850
Wire Wire Line
	6800 2900 7100 2900
Wire Wire Line
	7100 2900 7100 1800
Wire Wire Line
	7100 1800 3950 1800
Wire Wire Line
	3950 1800 3950 3650
Wire Wire Line
	3950 3650 2850 3650
Wire Wire Line
	2850 3750 3900 3750
Wire Wire Line
	3900 3750 3900 1750
Wire Wire Line
	3900 1750 7150 1750
Wire Wire Line
	7150 1750 7150 3000
Wire Wire Line
	7150 3000 6800 3000
Wire Wire Line
	6800 3100 7200 3100
Wire Wire Line
	7200 3100 7200 1600
Wire Wire Line
	7200 1600 3850 1600
Wire Wire Line
	3850 1600 3850 3850
Wire Wire Line
	3850 3850 2850 3850
Wire Wire Line
	2850 3950 3800 3950
Wire Wire Line
	3800 3950 3800 1550
Wire Wire Line
	3800 1550 7250 1550
Wire Wire Line
	7250 1550 7250 3200
Wire Wire Line
	7250 3200 6800 3200
Wire Wire Line
	6800 3300 7300 3300
Wire Wire Line
	7300 3300 7300 1500
Wire Wire Line
	7300 1500 3750 1500
Wire Wire Line
	3750 1500 3750 4600
Wire Wire Line
	3750 4600 3250 4600
Wire Wire Line
	3250 4600 3250 4850
Wire Wire Line
	3250 4850 2850 4850
Wire Wire Line
	2850 4950 3300 4950
Wire Wire Line
	3300 4950 3300 4650
Wire Wire Line
	3300 4650 3700 4650
Wire Wire Line
	3700 4650 3700 1450
Wire Wire Line
	3700 1450 7350 1450
Wire Wire Line
	7350 1450 7350 3400
Wire Wire Line
	7350 3400 6800 3400
Wire Wire Line
	6300 3400 5950 3400
Wire Wire Line
	5500 3400 5500 3250
Wire Wire Line
	5500 3250 2850 3250
Wire Wire Line
	2850 3150 5550 3150
Wire Wire Line
	5550 3300 6000 3300
Wire Wire Line
	2850 3050 5650 3050
Wire Wire Line
	5650 3050 5650 3200
Wire Wire Line
	5650 3200 6100 3200
Wire Wire Line
	2850 2750 5700 2750
Wire Wire Line
	5700 2750 5700 3100
Wire Wire Line
	5700 3100 6200 3100
$Comp
L Jumper:SolderJumper_3_Open JP3
U 1 1 5E83D895
P 6100 2400
F 0 "JP3" V 6054 2468 50  0000 L CNN
F 1 "IRQ" V 6145 2468 50  0000 L CNN
F 2 "Jumper:SolderJumper-3_P1.3mm_Open_RoundedPad1.0x1.5mm_NumberLabels" H 6100 2400 50  0001 C CNN
F 3 "~" H 6100 2400 50  0001 C CNN
	1    6100 2400
	0    1    1    0   
$EndComp
$Comp
L Jumper:SolderJumper_3_Open JP2
U 1 1 5E8410C6
P 5900 2850
F 0 "JP2" V 5854 2918 50  0000 L CNN
F 1 "EN" V 5945 2918 50  0000 L CNN
F 2 "Jumper:SolderJumper-3_P1.3mm_Open_RoundedPad1.0x1.5mm_NumberLabels" H 5900 2850 50  0001 C CNN
F 3 "~" H 5900 2850 50  0001 C CNN
	1    5900 2850
	0    1    1    0   
$EndComp
Wire Wire Line
	6300 3000 6050 3000
Wire Wire Line
	6050 3000 6050 3050
Wire Wire Line
	6050 3050 5900 3050
Wire Wire Line
	5900 2650 6000 2650
Wire Wire Line
	6000 2650 6000 2900
Wire Wire Line
	6000 2900 6300 2900
Wire Wire Line
	6100 2600 6100 2800
Wire Wire Line
	6100 2800 6300 2800
Wire Wire Line
	6300 2700 6300 2200
Wire Wire Line
	6300 2200 6100 2200
Wire Wire Line
	5750 2850 5300 2850
Wire Wire Line
	5300 2850 5300 2650
Wire Wire Line
	5300 2650 2850 2650
Wire Wire Line
	2850 2550 5350 2550
Wire Wire Line
	5350 2550 5350 2600
Wire Wire Line
	5350 2600 5800 2600
Wire Wire Line
	5800 2600 5800 2400
Wire Wire Line
	5800 2400 5950 2400
NoConn ~ 1650 2550
Wire Wire Line
	6300 2700 5600 2700
Connection ~ 6300 2700
Wire Wire Line
	5550 3150 5550 3300
Wire Wire Line
	6100 2600 5850 2600
Wire Wire Line
	5850 2600 5850 2550
Wire Wire Line
	5850 2550 5450 2550
Wire Wire Line
	5450 2550 5450 4050
Wire Wire Line
	5450 4050 6300 4050
Connection ~ 6100 2600
Wire Wire Line
	5900 2650 5350 2650
Wire Wire Line
	5350 2650 5350 4000
Wire Wire Line
	5350 4000 5400 4000
Wire Wire Line
	5400 4000 5400 4150
Wire Wire Line
	5400 4150 6300 4150
Connection ~ 5900 2650
Wire Wire Line
	6300 4250 5300 4250
Wire Wire Line
	5300 4250 5300 3000
Wire Wire Line
	5300 3000 5750 3000
Wire Wire Line
	5750 3000 5750 3050
Wire Wire Line
	5750 3050 5900 3050
Connection ~ 5900 3050
Wire Wire Line
	6300 4350 6200 4350
Wire Wire Line
	6200 4350 6200 3100
Connection ~ 6200 3100
Wire Wire Line
	6200 3100 6300 3100
Wire Wire Line
	6300 4450 6100 4450
Wire Wire Line
	6100 4450 6100 3200
Connection ~ 6100 3200
Wire Wire Line
	6100 3200 6300 3200
Wire Wire Line
	6300 4550 6000 4550
Wire Wire Line
	6000 4550 6000 3300
Connection ~ 6000 3300
Wire Wire Line
	6000 3300 6300 3300
$Comp
L Connector_Generic:Conn_02x09_Odd_Even J4
U 1 1 5E8D1DB7
P 6500 4350
F 0 "J4" H 6550 4967 50  0000 C CNN
F 1 "EXT BUS" H 6550 4876 50  0000 C CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_2x09_P2.54mm_Vertical" H 6500 4350 50  0001 C CNN
F 3 "~" H 6500 4350 50  0001 C CNN
	1    6500 4350
	1    0    0    -1  
$EndComp
Wire Wire Line
	6300 4650 5950 4650
Wire Wire Line
	5950 4650 5950 3400
Connection ~ 5950 3400
Wire Wire Line
	5950 3400 5500 3400
Wire Wire Line
	5900 3500 5900 4750
Wire Wire Line
	5900 4750 6300 4750
Connection ~ 5900 3500
Wire Wire Line
	5900 3500 5400 3500
Wire Wire Line
	6800 3950 7000 3950
Wire Wire Line
	7000 3950 7000 2700
Connection ~ 7000 2700
Wire Wire Line
	7050 2800 7050 4050
Wire Wire Line
	7050 4050 6800 4050
Connection ~ 7050 2800
Wire Wire Line
	7100 2900 7100 4150
Wire Wire Line
	7100 4150 6800 4150
Connection ~ 7100 2900
Wire Wire Line
	7150 3000 7150 4250
Wire Wire Line
	7150 4250 6800 4250
Connection ~ 7150 3000
Wire Wire Line
	6800 4350 7200 4350
Wire Wire Line
	7200 4350 7200 3100
Connection ~ 7200 3100
Wire Wire Line
	7250 3200 7250 4450
Wire Wire Line
	7250 4450 6800 4450
Connection ~ 7250 3200
Wire Wire Line
	6800 4550 7300 4550
Wire Wire Line
	7300 4550 7300 3300
Connection ~ 7300 3300
Wire Wire Line
	6800 4650 7350 4650
Wire Wire Line
	7350 4650 7350 3400
Connection ~ 7350 3400
Wire Wire Line
	7400 3500 7400 4750
Wire Wire Line
	7400 4750 6800 4750
Connection ~ 7400 3500
Wire Wire Line
	5600 2700 5600 3950
Wire Wire Line
	5600 3950 6300 3950
$Comp
L Device:R_POT_TRIM RV1
U 1 1 5E826212
P 3750 5050
F 0 "RV1" V 3543 5050 50  0000 C CNN
F 1 "Contrast" V 3634 5050 50  0000 C CNN
F 2 "Potentiometer_THT:Potentiometer_Piher_PT-10-V10_Vertical" H 3750 5050 50  0001 C CNN
F 3 "~" H 3750 5050 50  0001 C CNN
	1    3750 5050
	0    -1   -1   0   
$EndComp
Wire Wire Line
	2250 5250 4000 5250
Wire Wire Line
	3900 5050 4000 5050
Wire Wire Line
	4000 5050 4000 5250
Connection ~ 4000 5250
Wire Wire Line
	4000 5250 4300 5250
Wire Wire Line
	3600 5050 3400 5050
Wire Wire Line
	3400 5050 3400 2150
Connection ~ 3400 2150
Wire Wire Line
	3400 2150 4350 2150
Wire Wire Line
	4150 3650 4150 4550
$Comp
L Jumper:SolderJumper_3_Bridged12 JP1
U 1 1 5F12C2E7
P 4150 4700
F 0 "JP1" H 4150 4813 50  0000 C CNN
F 1 "Display Contrast" H 4150 4904 50  0000 C CNN
F 2 "Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm_NumberLabels" H 4150 4700 50  0001 C CNN
F 3 "~" H 4150 4700 50  0001 C CNN
	1    4150 4700
	1    0    0    1   
$EndComp
$EndSCHEMATC
