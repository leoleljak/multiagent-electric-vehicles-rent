import spade
import time
import datetime
import argparse
import asyncio
from spade.message import Message
from spade.template import Template

class Vehicle:
    def __init__(self, name, maxDistance, chargeTime, pricePerDay):
        self.name = name
        self.maxDistance = maxDistance
        self.charge = 100
        self.chargeTime = chargeTime
        self.pricePerDay = pricePerDay
        self.isReserved = False
        self.isCharging = False

    def printProperties(self): 
        print(self.name, "-", self.charge, "-", self.isReserved)
    
    def printChargeProperties(self): 
        print(self.name, "-", self.charge, "-", self.isCharging)

class RentStation(spade.agent.Agent):
    class MainBehaviour(spade.behaviour.CyclicBehaviour):
        async def on_start(self):
            print("I'm starting main behaviour")
            print("--------------")
            msg = Message(to="lleljak@rec.foi.hr")
            msg.set_metadata("performative", "inform")
            msg.set_metadata("ontology", "myOntology")
            msg.body = "registerStation"
            await self.send(msg)

        async def run(self):
            print("------ CHARGING BEHAVIOUR ------")
            self.printCurrentState()
            print("Waiting for requests by users ...")
            print("")
            
            ### Handle requests
            msg = await self.receive(timeout=100)
            if msg and msg.metadata:
                if msg.metadata["ontology"] == 'updateStationData':
                    self.agent.stations = msg.body.split(",")
                if msg.metadata["ontology"] == 'reserveVehicle':
                    vehicleName = msg.body
                    await self.reserveVehicle(vehicleName, msg.sender)
                if msg.metadata["ontology"] == 'collectVehicle':
                    vehicleName = msg.body.split(",")[0]
                    days = msg.body.split(",")[1]
                    await self.collectVehicle(vehicleName, int(days), msg.sender)
                if msg.metadata["ontology"] == 'returnVehicle':
                    vehicleName = msg.body.split(",")[0]
                    chargeLeft = msg.body.split(",")[1]
                    await self.returnVehicle(vehicleName, chargeLeft, msg.sender)

            print("")

        ### Print current state of station
        ###
        def printCurrentState(self):
            print("Station earnings:", self.agent.totalEarnings, "€")
            print("Current stations: ", self.agent.stations)
            print("")

            print("Cars:")
            print("Name - Charge - Reserved ")
            for car in self.agent.cars:
                car.printProperties()

            print("")
            print("Bikes:")
            print("Name - Charge - Reserved")
            for bike in self.agent.bikes: 
                bike.printProperties()

        ### Reserve vehicle for customer
        ###
        async def reserveVehicle(self, vehicleName, sender):
            for vehicle in self.agent.vehicles:
                if vehicle.name == vehicleName:
                    if not vehicle.isReserved and not vehicle.isCharging:
                        vehicle.isReserved = True
                    break
            reservationStation = str(self.agent.jid)

            msg = Message(to=sender.localpart + "@" + sender.domain)
            msg.set_metadata("performative", "inform")
            msg.set_metadata("ontology", "vehicleReserved")
            msg.body = reservationStation
            await self.send(msg)

        ### Customer collects vehicle
        ###
        async def collectVehicle(self, vehicleName, days, sender):
            for vehicle in self.agent.vehicles:
                if vehicle.name == vehicleName:
                    self.agent.totalEarnings += days * vehicle.pricePerDay
                    break

            msg = Message(to=sender.localpart + "@" + sender.domain)
            msg.set_metadata("performative", "inform")
            msg.set_metadata("ontology", "vehicleCollected")
            msg.body = str(self.agent.totalEarnings)
            await self.send(msg)

        ### Customer returns vehicle
        ###
        async def returnVehicle(self, vehicleName, chargeLeft, sender):
            for vehicle in self.agent.vehicles:
                if vehicle.name == vehicleName:
                    vehicle.charge = int(float(chargeLeft))
                    vehicle.isCharging = True
                    vehicle.isReserved = False
                    break

            msg = Message(to=sender.localpart + "@" + sender.domain)
            msg.set_metadata("performative", "inform")
            msg.set_metadata("ontology", "vehicleReturned")
            msg.body = vehicleName
            await self.send(msg)

    class ChargingBehaviour(spade.behaviour.PeriodicBehaviour):
        async def on_start(self):
            print("I'm starting charging behaviour")

        async def run(self):
            print("------ CHARGING BEHAVIOUR ------")
            self.printCurrentState()
            
            needsCharging = False
            ### Charge vehicles if needed
            for vehicle in self.agent.vehicles:
                if vehicle.charge < 100:
                    needsCharging = True
                    break
                
            if needsCharging:
                await asyncio.sleep(20)
                for vehicle in self.agent.vehicles:
                    vehicle.charge = 100
                    vehicle.isCharging = False
                print("All vehicles charged")
            else:
                print("No need to charge vehicles")

            print("")
                
        ### Print current charging state
        ###
        def printCurrentState(self):
            print("")

            print("Cars:")
            print("Name - Charge - isCharging ")
            for car in self.agent.cars:
                car.printChargeProperties()

            print("")
            print("Bikes:")
            print("Name - Charge - isCharging")
            for bike in self.agent.bikes: 
                bike.printChargeProperties()


    async def setup(self):
        print("Setting up rent station system...")
        self.stations = []
        self.totalEarnings = 0
        self.cars = self.setupCars()
        self.bikes = self.setupBikes()
        self.vehicles = self.cars + self.bikes
        mainBehaviour = self.MainBehaviour()
        chargingBehaviour = self.ChargingBehaviour(period=15)
        template = Template()
        template.set_metadata("performative", "inform")
        self.add_behaviour(mainBehaviour, template)
        self.add_behaviour(chargingBehaviour)

    def setupCars(self):
        return [
            Vehicle("nissan", 300, 100, 15),
            Vehicle("mazda", 250, 50, 12),
            Vehicle("mercedes", 400, 150, 20)
        ]

    def setupBikes(self):
        return [
            Vehicle("trek", 100, 50, 5),
            Vehicle("greyp", 150, 30, 7),
            Vehicle("ktm", 200, 20, 10)
        ]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-jid", type=str, help="ID")
    parser.add_argument("-pwd", type=str, help="Password")
    args = parser.parse_args()
    a = RentStation(args.jid, args.pwd)
    print("Current jid: ", a.jid)
    a.start()
    #a.web.start(hostname="127.0.0.1", port="10000")
    input("Press ENTER to exit.\n")
    print()
    a.stop()
    spade.quit_spade()
