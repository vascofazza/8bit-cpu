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
L Connector_Generic:Conn_01x08 J1
U 1 1 5E7F3AE4
P 4500 5300
F 0 "J1" V 4372 4812 50  0000 R CNN
F 1 "Signals" V 4463 4812 50  0000 R CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical" H 4500 5300 50  0001 C CNN
F 3 "~" H 4500 5300 50  0001 C CNN
	1    4500 5300
	0    -1   1    0   
$EndComp
$Comp
L Connector_Generic:Conn_01x02 J3
U 1 1 5E7F8A6C
P 6200 4500
F 0 "J3" H 6280 4492 50  0000 L CNN
F 1 "Power" H 6280 4401 50  0000 L CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" H 6200 4500 50  0001 C CNN
F 3 "~" H 6200 4500 50  0001 C CNN
	1    6200 4500
	1    0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_02x09_Odd_Even J4
U 1 1 5E7F9439
P 4600 4600
F 0 "J4" V 4696 4112 50  0000 R CNN
F 1 "Conn_02x09_Odd_Even" V 4605 4112 50  0000 R CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_2x09_P2.54mm_Vertical" H 4600 4600 50  0001 C CNN
F 3 "~" H 4600 4600 50  0001 C CNN
	1    4600 4600
	0    -1   -1   0   
$EndComp
Wire Wire Line
	4200 4000 4200 4300
Wire Wire Line
	4300 4000 4300 4300
Wire Wire Line
	4400 4000 4400 4300
Wire Wire Line
	4500 4000 4500 4300
Wire Wire Line
	4600 4000 4600 4300
Wire Wire Line
	4700 4000 4700 4300
Wire Wire Line
	4800 4000 4800 4300
Wire Wire Line
	4900 4000 4900 4300
Wire Wire Line
	4200 5100 4200 4800
Wire Wire Line
	4300 5100 4300 4800
Wire Wire Line
	4400 5100 4400 4800
Wire Wire Line
	4500 5100 4500 4800
Wire Wire Line
	4600 5100 4600 4800
Wire Wire Line
	4700 5100 4700 4800
Wire Wire Line
	4800 5100 4800 4800
Wire Wire Line
	4900 5100 4900 4800
Wire Wire Line
	6000 4800 5000 4800
Wire Wire Line
	5000 4300 6000 4300
Wire Wire Line
	6000 4300 6000 4500
$Comp
L Connector_Generic:Conn_01x08 J2
U 1 1 5E7F6C54
P 4500 3800
F 0 "J2" V 4464 3312 50  0000 R CNN
F 1 "BUS" V 4373 3312 50  0000 R CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical" H 4500 3800 50  0001 C CNN
F 3 "~" H 4500 3800 50  0001 C CNN
	1    4500 3800
	0    -1   -1   0   
$EndComp
Wire Wire Line
	6000 4600 6000 4800
$EndSCHEMATC
