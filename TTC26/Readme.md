# The Things Conference 2026

Demo-related resources

Demo setup explanation follows

## LoRaWAN and Web of Things

Devices:

- Adeunis Comfort
  - Publish interval: 11min
- Milesight em300 zld
  - Publish interval: 15 min
- Netvox R718a
  - Publish interval: 60 min

### Keynote

### Booth

## Zenoh and Web of Things

### Workshop

Link: https://www.thethingsconference.com/program/agenda-overview/recz7w6jmuzpktdag
Location: Workshop 2
Time and Day: Tuesday 22 September at 14:00
Setup: Q&A during the talks or after? Do we have time before to setup the hardware

1. Phani: Introduce Zenoh (15 min)
2. Ege: Onboard a SentronPAC without WoT (10 min)
   0. Show an existing dashboard about energy usage. Need to add a new device.  
   1. Show PDF, explain that it is Modbus. Not OLD!
   2. Start installing modbus library, understand how to use it, reference registers from PDF
   3. Start sending values to Zenoh with python. 10 lines of code but understanding the protocolS and their libraries
   4. Add brick:energyMeter annotation in the data so that the dashboard can group them. Change units to Volts that dashboard uses.
4. Kirill: Onboard a SentronPAC with WoT (15 min)
   1. Show the TM. Comes from Manufacturer. Open standard. Tease TMC. Already has `brick:energyMeter` and units annotations as the manufacturer knows it best
   2. For a target system, we can automate: iterate through properties etc.
   3. Show onboarding UI. Drag and drop. Show data in Zenoh automatically
5. (if time allows) Kirill: Extending to other protocols
   1. We have Lorawan Devices as well. Now we can apply the same principle
   2. Show devices from the booth
  
### Booth
