class RecipeEngineCore:
    def __init__(self):
        self.items = {}
        self.recipes = {}
        self.named_rules = {}
        self.unnamed_rules = set()