class HotkeyCombination:
    def __init__(self, hotkey_combination:str):
        self.hotkey_combination = hotkey_combination

    @property
    def mac(self):
        return '+'.join([f'<{x.lower()}>' for x in self.hotkey_combination.split('+')])

    @property
    def win(self):
        return self.hotkey_combination.lower()

    def __repr__(self):
        return '+'.join([f'{x.capitalize()}' for x in self.hotkey_combination.split('+')])
