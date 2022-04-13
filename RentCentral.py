import spade
import time
import datetime
from spade.message import Message
from spade.template import Template

class RentCentral(spade.agent.Agent):
    class MainBehaviour(spade.behaviour.CyclicBehaviour):
        async def on_start(self):
            print("I'm starting central behaviour")
            print("--------------")

        async def run(self):
            print("Current stations: ", self.agent.stations)
            print("--------------")
            print("Waiting for requests by stations ...")
            
            msg = await self.receive(timeout=100)
            if msg:
                if msg.body == 'registerStation':
                    self.agent.stations.append(msg.sender)
                    await self.updateStations()
                
            print("")
        
        ### Notify all stations with current stations that are registered
        ###
        async def updateStations(self):
            allStationIDs = []
            for station in self.agent.stations:
                allStationIDs.append(station.localpart + "@" + station.domain)

            for station in self.agent.stations:
                receiver = station.localpart + "@" + station.domain
                msg = Message(to=receiver)
                msg.set_metadata("performative", "inform")
                msg.set_metadata("ontology", "updateStationData")
                msg.body = ",".join(allStationIDs)
                await self.send(msg)

    async def setup(self):
        print("Setting up central rent system...")
        self.stations = []
        mainBehaviour = self.MainBehaviour()
        template = Template()
        template.set_metadata("performative", "inform")
        self.add_behaviour(mainBehaviour, template)

if __name__ == '__main__':
    a = RentCentral("lleljak@rec.foi.hr", "lleljak1")
    a.start()
    a.web.start(hostname="127.0.0.1", port="10000")
    input("Press ENTER to exit.\n")
    print()
    a.stop()
    spade.quit_spade()
