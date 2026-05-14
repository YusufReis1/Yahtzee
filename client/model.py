import random
from collections import Counter


class Category:

    def score(self, dice: list[int]) -> int:
        raise NotImplementedError

    def yahtzee_bonus_override_score(self, dice: list[int]) -> int:
        raise NotImplementedError

    @property
    def name(self) -> str:
        raise NotImplementedError

    @staticmethod
    def get_category(index: int) -> "Category":
        if 1 <= index <= 6:
            return UpperCategory(index)
        mapping = {
            7:  ThreeOfAKind,
            8:  FourOfAKind,
            9:  FullHouse,
            10: SmallStraight,
            11: LargeStraight,
            12: Chance,
            13: Yahtzee,
        }
        if index in mapping:
            return mapping[index]()
        raise ValueError(f"Invalid category index: {index}")

    @staticmethod
    def _is_yahtzee(dice: list[int]) -> bool:
        return len(set(dice)) == 1


class UpperCategory(Category):
    def __init__(self, target: int):
        self.target = target

    def score(self, dice):
        return sum(d for d in dice if d == self.target)

    def yahtzee_bonus_override_score(self, dice):
        return 0

    @property
    def name(self):
        return ["Ones", "Twos", "Threes", "Fours", "Fives", "Sixes"][self.target - 1]


class ThreeOfAKind(Category):
    @property
    def name(self): return "Three of a Kind"

    def score(self, dice):
        counts = Counter(dice)
        if any(v >= 3 for v in counts.values()):
            return sum(dice)
        return 0

    def yahtzee_bonus_override_score(self, dice):
        return self.score(dice)


class FourOfAKind(Category):
    @property
    def name(self): return "Four of a Kind"

    def score(self, dice):
        counts = Counter(dice)
        if any(v >= 4 for v in counts.values()):
            return sum(dice)
        return 0

    def yahtzee_bonus_override_score(self, dice):
        return self.score(dice)


class FullHouse(Category):
    @property
    def name(self): return "Full House"

    def score(self, dice):
        counts = sorted(Counter(dice).values())
        if counts == [2, 3]:
            return 25
        return 0

    def yahtzee_bonus_override_score(self, dice):
        return 25


class SmallStraight(Category):
    @property
    def name(self): return "Small Straight"

    def score(self, dice):
        unique = sorted(set(dice))
        straights = [{1,2,3,4}, {2,3,4,5}, {3,4,5,6}]
        for s in straights:
            if s.issubset(set(unique)):
                return 30
        return 0

    def yahtzee_bonus_override_score(self, dice):
        return 30


class LargeStraight(Category):
    @property
    def name(self): return "Large Straight"

    def score(self, dice):
        unique = sorted(set(dice))
        if unique in [[1,2,3,4,5], [2,3,4,5,6]]:
            return 40
        return 0

    def yahtzee_bonus_override_score(self, dice):
        return 40


class Chance(Category):
    @property
    def name(self): return "Chance"

    def score(self, dice):
        return sum(dice)

    def yahtzee_bonus_override_score(self, dice):
        return self.score(dice)


class Yahtzee(Category):
    @property
    def name(self): return "Yahtzee"

    def score(self, dice):
        return 50 if self._is_yahtzee(dice) else 0

    def yahtzee_bonus_override_score(self, dice):
        return 50



class Die:
    def __init__(self):
        self.value = 1
        self.held  = False

    def roll(self):
        if not self.held:
            self.value = random.randint(1, 6)



class ScoreEntry:
    def __init__(self, category: Category):
        self.category = category
        self.chosen   = False
        self.score    = 0



class Player:
    def __init__(self, name: str):
        self.name           = name
        self.upper_score    = 0
        self.lower_score    = 0
        self.upper_bonus    = 0
        self.yahtzee_bonus  = 0
        self.have_yahtzee   = False

    def add_score(self, pts: int, is_upper: bool):
        if is_upper:
            self.upper_score += pts
        else:
            self.lower_score += pts

    def add_upper_bonus(self):
        self.upper_bonus  += 35
        self.upper_score  += 35

    def add_yahtzee_bonus(self):
        self.yahtzee_bonus += 100

    @property
    def total(self) -> int:
        return self.upper_score + self.lower_score + self.yahtzee_bonus

    def reset(self):
        self.upper_score   = 0
        self.lower_score   = 0
        self.upper_bonus   = 0
        self.yahtzee_bonus = 0
        self.have_yahtzee  = False



class Game:
    NUM_CATEGORIES = 13

    def __init__(self, player_name: str):
        self.player    = Player(player_name)
        self.dice      = [Die() for _ in range(5)]
        self.entries   = [ScoreEntry(Category.get_category(i + 1))
                          for i in range(self.NUM_CATEGORIES)]
        self.roll_count = 0


    @property
    def dice_values(self) -> list[int]:
        return [d.value for d in self.dice]

    def _is_yahtzee(self) -> bool:
        return len(set(self.dice_values)) == 1

    def roll_dice(self):
        if self.roll_count >= 3:
            return
        if self.roll_count == 0:
            for d in self.dice:
                d.held = False
        for d in self.dice:
            d.roll()
        self.roll_count += 1
        if self._is_yahtzee() and self.player.have_yahtzee:
            self.player.add_yahtzee_bonus()

    def normal_selectable(self) -> list[int]:
        vals = self.dice_values
        if self._is_yahtzee() and self.entries[12].chosen:
            num        = vals[0]
            upper_idx  = num - 1
            if not self.entries[upper_idx].chosen:
                return [upper_idx]
        return [i for i in range(13) if not self.entries[i].chosen]

    def override_selectable(self) -> list[int]:
        vals = self.dice_values
        if not (self._is_yahtzee() and self.entries[12].chosen):
            return []
        num       = vals[0]
        upper_idx = num - 1
        if not self.entries[upper_idx].chosen:
            return []
        lower = [i for i in range(6, 13) if not self.entries[i].chosen]
        if lower:
            return lower
        return [i for i in range(6) if not self.entries[i].chosen]

    def get_possible_score(self, idx: int, use_override: bool) -> int:
        cat = self.entries[idx].category
        if use_override:
            return cat.yahtzee_bonus_override_score(self.dice_values)
        return cat.score(self.dice_values)

    def select_category(self, idx: int, use_override: bool):
        entry = self.entries[idx]
        if entry.chosen:
            return
        pts = self.get_possible_score(idx, use_override)
        entry.score  = pts
        entry.chosen = True
        self.player.add_score(pts, idx < 6)
        if idx == 12 and pts == 50:
            self.player.have_yahtzee = True
        if self.player.upper_bonus == 0 and self.player.upper_score >= 63:
            self.player.add_upper_bonus()

    def is_game_over(self) -> bool:
        return all(e.chosen for e in self.entries)

    def reset(self):
        self.player.reset()
        for d in self.dice:
            d.value = 1
            d.held  = False
        self.entries    = [ScoreEntry(Category.get_category(i + 1))
                           for i in range(self.NUM_CATEGORIES)]
        self.roll_count = 0
