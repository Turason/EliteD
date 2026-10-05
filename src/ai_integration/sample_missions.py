"""Illustrative mission-board fixtures for NPC prompt and behavior testing.

Rewards, locations, and availability are sample values, not live game data.
"""

from typing import Dict, List, Tuple

from .models import MissionOffer, NPCType


MissionFixture = Tuple[str, str, str, str, str, int, str, str]


def _offers(*rows: MissionFixture) -> List[MissionOffer]:
    return [MissionOffer(*row) for row in rows]


TEST_MISSIONS: Dict[NPCType, List[MissionOffer]] = {
    NPCType.TRADER: _offers(
        ("Courier: Market Intelligence", "Data delivery", "Deliver sealed market data to a partner station. No cargo space is needed, but deliver it before the contract expires.", "Independent Pilots' Cooperative", "LHS 3447", 85000, "Low", "Small or fast ship recommended"),
        ("Source and Return: Consumer Technology", "Source and return", "Purchase the requested consumer technology on the open market and bring it back. The broker pays on delivery.", "LHS 3447 Commodities Exchange", "LHS 3447", 420000, "Low", "Cargo capacity required; purchase cost is not included in the reward"),
        ("Delivery: Medical Supplies", "Commodity delivery", "Carry medical supplies to a station facing a shortfall and confirm delivery with its market office.", "Independent Pilots' Cooperative", "Eranin", 310000, "Low", "Cargo capacity required"),
    ),
    NPCType.PIRATE: _offers(
        ("Massacre Contract: Security Forces", "Massacre", "A local criminal faction wants rival security ships driven out of the system. Only qualifying targets count toward the contract.", "Black Flight Collective", "Anarchy system near LHS 3447", 680000, "High", "Combat-capable ship recommended; check the target faction before engaging"),
        ("Source and Return: Restricted Weapons", "Source and return", "Acquire a small shipment of restricted weapons and deliver it discreetly to a contact at an anarchy outpost.", "Black Flight Collective", "Fujin", 540000, "High", "Cargo capacity required; illegal cargo may attract security attention"),
        ("Salvage: Recover a Black Box", "Salvage recovery", "Locate a signal source, recover a black box from the wreckage, and return it to the criminal contact.", "Sirius Special Activities", "Wolf 359", 275000, "Medium", "Bring a cargo scoop; the signal source may be guarded"),
    ),
    NPCType.EXPLORER: _offers(
        ("Survey: Map the Planetary Surface", "Planetary scan", "Travel to the marked body and scan the designated surface installation for survey data.", "Universal Cartographics Liaison", "HIP 20277", 390000, "Medium", "Detailed Surface Scanner recommended; planetary approach required"),
        ("Salvage: Geological Samples", "Planetary salvage", "Search the reported surface site for geological samples and return the recovered data to the issuing faction.", "Independent Explorers' Guild", "Synuefe XR-H d11-102", 240000, "Medium", "Planetary landing and cargo space may be required"),
        ("Passenger: Scenic System Tour", "Sightseeing passenger", "Take a small group of sightseers to the listed beacon, then return them safely to the station.", "Independent Explorers' Guild", "V886 Centauri", 510000, "Low", "Passenger cabin required; follow the listed route"),
    ),
    NPCType.BOUNTY_HUNTER: _offers(
        ("Massacre Contract: Wanted Pirates", "Massacre", "Eliminate the specified number of wanted ships belonging to a pirate faction in the target system.", "Wolf 359 Security Office", "Wolf 359", 760000, "High", "Combat-capable ship recommended; targets must be wanted"),
        ("Assassination: Pirate Lieutenant", "Assassination", "Locate and eliminate a named pirate target reported operating in the system.", "LHS 3447 Security Office", "LHS 3447", 620000, "High", "Combat-capable ship recommended; confirm the target identity"),
        ("Survey: Locate a Wanted Contact", "Planetary scan", "Scan the marked surface installation for records that may identify wanted criminal activity.", "Independent Security Force", "Eranin", 330000, "Medium", "Planetary approach required; defensive equipment recommended"),
    ),
    NPCType.FEDERAL_NAVY: _offers(
        ("Federal Navy Courier Orders", "Data delivery", "Carry sealed operational data to a Federal-aligned contact before the dispatch window closes.", "Federal Navy Auxiliary", "Sol", 180000, "Low", "Federal-aligned access may be required"),
        ("Federal Navy Combat Contract", "Massacre", "Support Federal forces by defeating the stated number of ships from the opposing faction in the conflict system.", "Federal Navy Auxiliary", "Leesti", 920000, "High", "Combat-capable ship recommended; choose the Federal side"),
        ("Federal Navy Reconnaissance", "Planetary scan", "Scan the marked installation and return its security data to the Federal mission contact.", "Federal Navy Auxiliary", "Ross 128", 460000, "Medium", "Planetary approach required; hostile response possible"),
    ),
    NPCType.IMPERIAL_NAVY: _offers(
        ("Imperial Navy Dispatch", "Data delivery", "Deliver encrypted dispatches to an Imperial liaison at the destination station.", "Imperial Navy Auxiliary", "Achenar", 175000, "Low", "Imperial-aligned access may be required"),
        ("Imperial Navy Combat Contract", "Massacre", "Aid Imperial forces by defeating the stated number of ships from the opposing faction in the conflict system.", "Imperial Navy Auxiliary", "Cemiess", 940000, "High", "Combat-capable ship recommended; choose the Imperial side"),
        ("Imperial Navy Reconnaissance", "Planetary scan", "Scan the specified surface installation and return its intelligence to the Imperial contact.", "Imperial Navy Auxiliary", "LFT 926", 445000, "Medium", "Planetary approach required; hostile response possible"),
    ),
    NPCType.ALLIANCE: _offers(
        ("Alliance Relief Shipment", "Commodity delivery", "Deliver food and basic medicines to an Alliance-supported station experiencing shortages.", "Alliance Office of Statistics", "Alioth", 365000, "Low", "Cargo capacity required"),
        ("Alliance Defense Contract", "Massacre", "Defend the local faction by defeating the specified opposing ships during the system conflict.", "Alliance Defense Force", "Lave", 810000, "High", "Combat-capable ship recommended; verify the supported faction"),
        ("Alliance Courier Run", "Data delivery", "Carry diplomatic correspondence to an Alliance representative at the destination station.", "Alliance Office of Statistics", "Diso", 155000, "Low", "Fast ship recommended"),
    ),
    NPCType.ENGINEER: _offers(
        ("Workshop Requisition: Conductive Components", "Material requisition", "Collect the requested engineering materials from appropriate sources and bring them to the workshop contact.", "Felicity Farseer Workshop", "Deciat", 125000, "Medium", "Material requirements must be checked with the engineer; this is a test requisition"),
        ("Survey: Scan a Geological Site", "Planetary scan", "Scan the marked geological site and return the measurements for a workshop research project.", "Independent Workshop Consortium", "Khun", 285000, "Medium", "Planetary approach required; Detailed Surface Scanner recommended"),
        ("Courier: Experimental Data", "Data delivery", "Deliver a sealed data package between engineering contacts without altering its contents.", "Independent Workshop Consortium", "Farseer Inc", 190000, "Low", "No cargo capacity required"),
    ),
    NPCType.CITIZEN: _offers(
        ("Courier: Personal Correspondence", "Data delivery", "Take a private message to a relative at the destination station and confirm delivery.", "Local Residents' Association", "Eranin", 42000, "Low", "Small or fast ship recommended"),
        ("Delivery: Emergency Food Supplies", "Commodity delivery", "Bring food to a nearby settlement whose regular supply shipment has been delayed.", "Local Residents' Association", "Maujinagau", 135000, "Low", "Cargo capacity required"),
        ("Passenger: Evacuate Residents", "Passenger evacuation", "Transport residents from a threatened station to the listed safe port.", "Local Rescue Service", "Sol", 275000, "Medium", "Passenger cabins required; return passengers safely"),
    ),
}
