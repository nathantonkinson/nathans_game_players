#this is the base class all units should inherit, both built-in and custom


class Unit:
    def __init__(self, unit_type): #want to pass stuff in here?
        # self.name = "empty"
        self.health = 10
        self.healthMax = self.health
        self.veterancy = 0 #0, 1, 2
        # self.value = 100
        self.xp = 0
        # self.hex = None #idk if we want to store this here, I'd rather have the hex point to the unit class instance
        self.type = unit_type

    def take_damage(self, damage):
        pass

    def is_alive(self):
        return self.health > 0
    
class UnitHeavyGround(Unit):
    def __init__(self):
        super().__init__("HeavyGround")
        self.forestcost = 3
