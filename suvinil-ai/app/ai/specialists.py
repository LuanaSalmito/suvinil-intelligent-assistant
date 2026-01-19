from typing import Dict
from app.models.paint import Environment


class BaseSpecialist:
    name: str = ""

    def can_handle(self, slots: Dict) -> bool:
        raise NotImplementedError

    def consult(self, slots: Dict) -> Dict:
        raise NotImplementedError


class ExternalEnvironmentSpecialist(BaseSpecialist):
    name = "ambientes externos"

    def can_handle(self, slots: Dict) -> bool:
        return slots.get("environment") == Environment.EXTERIOR.value

    def consult(self, slots: Dict) -> Dict:
        if not slots.get("surface_type"):
            return {
                "needs_more_info": True,
                "reasoning": "Você pode me dizer qual é a superfície da fachada?"
            }

        return {
            "needs_more_info": False,
            "priority": "external"
        }


class WoodSpecialist(BaseSpecialist):
    name = "superfícies de madeira"

    def can_handle(self, slots: Dict) -> bool:
        return slots.get("surface_type") == "madeira"

    def consult(self, slots: Dict) -> Dict:
        return {
            "needs_more_info": False,
            "priority": "wood"
        }


ALL_SPECIALISTS = [
    ExternalEnvironmentSpecialist(),
    WoodSpecialist()
]
