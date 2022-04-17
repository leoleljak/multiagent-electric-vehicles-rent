import time
import spade
import argparse
import random
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from spade.message import Message

RESERVE_VEHICLE = "RESERVE_VEHICLE"
COLLECT_VEHICLE = "COLLECT_VEHICLE"
USE_VEHICLE = "USE_VEHICLE"
CHARGE_VEHICLE = "CHARGE_VEHICLE"
RETURN_VEHICLE = "RETURN_VEHICLE"

STATION_ADDRESS = "@rec.foi.hr"

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

class RentVehicleBehaviour(FSMBehaviour):
    async def on_start(self):
        print(f"Starting at initial state {self.current_state}")

    async def on_end(self):
        print(f"Finished at state {self.current_state}")
        await self.agent.stop()

class ReserveVehicle(State):
    async def run(self):
        ## Tell station that you want to reserve it - if it's unavailable station will give you
        ## other station from list.
        ##
        print("------ RESERVE VEHICLE ------ ")
        print("Going to collect vehicle at station -", self.agent.station, STATION_ADDRESS)
        msg = Message(to=self.agent.station + STATION_ADDRESS)
        msg.set_metadata("performative", "inform")
        msg.set_metadata("ontology", "reserveVehicle")
        msg.body = self.agent.vehicle
        await self.send(msg)
        print("Waiting for response...")
        msgReceived = await self.receive(timeout=10000)
        self.agent.station = msgReceived.body

        if msgReceived and msgReceived.metadata:
            if msgReceived.metadata["ontology"] == 'vehicleReserved':
                print("Vehicle ", self.agent.vehicle, " is reserved at station ", msgReceived.body)
                print("Going to station ...")
                time.sleep(2)
                self.set_next_state(COLLECT_VEHICLE)
            elif msgReceived.metadata["ontology"] == 'noOtherStations':
                print("No other stations available, finishing agent...")
                time.sleep(2)
                self.kill()
            elif msgReceived.metadata["ontology"] == 'otherStation':
                self.agent.station = msgReceived.body
                self.set_next_state(RESERVE_VEHICLE)

class CollectVehicle(State):
    async def run(self):
        ## Tell station that you collected vehicle and pay at advance
        ##
        print("\n------ COLLECT VEHICLE ------ ")
        print("Arrived at station")
        msg = Message(to=self.agent.station)
        msg.set_metadata("performative", "inform")
        msg.set_metadata("ontology", "collectVehicle")
        msg.body = ",".join([self.agent.vehicle, self.agent.days])
        await self.send(msg)
        
        print("Waiting for response...")
        msgReceived = await self.receive(timeout=10000)
        print("Vehicle is collected and rent is payed", msgReceived.body, "€")

        self.set_next_state(USE_VEHICLE)

class UseVehicle(State):
    async def run(self):
        ## Random usage, random charging after it's used and etc
        ## From this state to Charge or to ReturnVehicle
        ##
        print("\n------ USE VEHICLE ------ ")
        print("I'm using vehicle")
        
        for vehicleF in self.agent.vehicles:
            if vehicleF.name == self.agent.vehicle:
                vehicleChargeTime = vehicleF.chargeTime / 10
                vehicleRange = vehicleF.maxDistance
                break

        fullRangeTime = vehicleRange/10
        time.sleep(fullRangeTime)
        print("Vehicle fully discharged")
        self.agent.daysRemaining -= fullRangeTime
        print("Rent time remaining:", self.agent.daysRemaining)

        if self.agent.daysRemaining >= fullRangeTime + vehicleChargeTime:
            self.set_next_state(CHARGE_VEHICLE)    
        else:
            self.set_next_state(RETURN_VEHICLE)    

class ChargeVehicle(State):
    async def run(self):
        ## Charging the vehicle
        ##
        print("\n------ CHARGE VEHICLE ------ ")
        print("I'm charging vehicle")
        for vehicle in self.agent.vehicles:
            if vehicle.name ==  self.agent.vehicle:
                vehicleChargeTime = vehicle.chargeTime / 10
        time.sleep(vehicleChargeTime)
        self.agent.daysRemaining -= vehicleChargeTime
        print("Vehicle charged to 100%")
        print("Rent time remaining:", self.agent.daysRemaining)
        self.set_next_state(USE_VEHICLE)

class ReturnVehicle(State):
    async def run(self):
        ## Tell station that you are giving it back and how much charge is left
        ##
        print("\n------ RETURN VEHICLE ------ ")
        print("I'm returning vehicle")
        msg = Message(to=self.agent.station)
        msg.set_metadata("performative", "inform")
        msg.set_metadata("ontology", "returnVehicle")
        msg.body = ",".join([self.agent.vehicle, str(self.agent.daysRemaining)])
        print("Returning vehicle", self.agent.vehicle, "with charge left:", self.agent.daysRemaining)
        await self.send(msg)
        
        print("Waiting for response...")
        msgReceived = await self.receive(timeout=10000)
        print("Vehicle returned succesfully, heading home...")
        time.sleep(2)

class RentUser(Agent):
    async def setup(self):
        station = ""
        vehicle = ""
        days = 0
        daysRemaining = 0
        self.vehicles = self.setupCars() + self.setupBikes()

        fsm = RentVehicleBehaviour()
        fsm.add_state(name=RESERVE_VEHICLE, state=ReserveVehicle(), initial=True)
        fsm.add_state(name=COLLECT_VEHICLE, state=CollectVehicle())
        fsm.add_state(name=USE_VEHICLE, state=UseVehicle())
        fsm.add_state(name=CHARGE_VEHICLE, state=ChargeVehicle())
        fsm.add_state(name=RETURN_VEHICLE, state=ReturnVehicle())

        fsm.add_transition(source=RESERVE_VEHICLE, dest=COLLECT_VEHICLE)
        fsm.add_transition(source=RESERVE_VEHICLE, dest=RESERVE_VEHICLE)
        fsm.add_transition(source=COLLECT_VEHICLE, dest=USE_VEHICLE)
        fsm.add_transition(source=USE_VEHICLE, dest=CHARGE_VEHICLE)
        fsm.add_transition(source=USE_VEHICLE, dest=RETURN_VEHICLE)
        fsm.add_transition(source=CHARGE_VEHICLE, dest=USE_VEHICLE)
        fsm.add_transition(source=CHARGE_VEHICLE, dest=RETURN_VEHICLE)
        self.add_behaviour(fsm)

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-jid", type=str, help="ID")
    parser.add_argument("-pwd", type=str, help="Password")
    parser.add_argument("-station", type=str, help="Station id")
    parser.add_argument("-vehicle", type=str, help="Vehicle name")
    parser.add_argument("-days", type=str, help="Days to rent")
    
    args = parser.parse_args()
    a = RentUser(args.jid, args.pwd)
    a.station = args.station.strip()
    a.vehicle = args.vehicle.strip()
    a.days = args.days
    a.daysRemaining = int(a.days) * 100

    a.start()
    #a.web.start(hostname="127.0.0.1", port="10000")
    input("Press ENTER to exit.\n")
    print()
    a.stop()
    spade.quit_spade()