import spade
import time
import datetime
import argparse
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

    def printProperties(self): 
        print(self.name, "-", self.charge, "-", self.isReserved)

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
            self.printCurrentState()
            print("--------------")
            print("Waiting for requests by users ...")
            
            ### Handle requests
            msg = await self.receive(timeout=100)
            if msg and msg.metadata:
                if msg.metadata["ontology"] == 'updateStationData':
                    self.agent.stations = msg.body.split(",")
            print("")

        ### Print current state of vehicles 
        ###
        def printCurrentState(self):
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

    async def setup(self):
        print("Setting up rent station system...")
        self.stations = []
        self.cars = self.setupCars()
        self.bikes = self.setupBikes()
        mainBehaviour = self.MainBehaviour()
        template = Template()
        template.set_metadata("performative", "inform")
        self.add_behaviour(mainBehaviour, template)

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
    a.start()
    #a.web.start(hostname="127.0.0.1", port="10000")
    input("Press ENTER to exit.\n")
    print()
    a.stop()
    spade.quit_spade()
