import numpy as np
import pandas as pd
import requests
import random
import tkinter as tk
from tkinter import ttk, messagebox
from enum import Enum
from typing import List, Dict, Tuple

class PokemonType(Enum):
    FIRE = "Fire"
    WATER = "Water"
    GRASS = "Grass"
    ELECTRIC = "Electric"
    NORMAL = "Normal"

class Move:
    def __init__(self, name: str, power: int, move_type: PokemonType, accuracy: float = 1.0):
        self.name = name
        self.power = power
        self.type = move_type
        self.accuracy = accuracy

class Pokemon:
    def __init__(self, name: str, pokemon_type: PokemonType, hp: int, attack: int, defense: int, speed: int, moves: List[Move]):
        self.name = name
        self.type = pokemon_type
        self.max_hp = hp
        self.current_hp = hp
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.moves = moves
    
    def is_alive(self) -> bool:
        return self.current_hp > 0
    
    def take_damage(self, damage: int):
        self.current_hp = max(0, self.current_hp - damage)
    
    def heal(self, amount: int):
        self.current_hp = min(self.max_hp, self.current_hp + amount)
    
    def get_hp_percentage(self) -> float:
        return (self.current_hp / self.max_hp) * 100

class TypeEffectiveness:
    CHART = {
        PokemonType.FIRE: {
            PokemonType.GRASS: 2.0,
            PokemonType.WATER: 0.5,
            PokemonType.FIRE: 0.5,
            PokemonType.ELECTRIC: 1.0,
            PokemonType.NORMAL: 1.0
        },
        PokemonType.WATER: {
            PokemonType.FIRE: 2.0,
            PokemonType.GRASS: 0.5,
            PokemonType.WATER: 0.5,
            PokemonType.ELECTRIC: 1.0,
            PokemonType.NORMAL: 1.0
        },
        PokemonType.GRASS: {
            PokemonType.WATER: 2.0,
            PokemonType.FIRE: 0.5,
            PokemonType.GRASS: 0.5,
            PokemonType.ELECTRIC: 1.0,
            PokemonType.NORMAL: 1.0
        },
        PokemonType.ELECTRIC: {
            PokemonType.WATER: 2.0,
            PokemonType.GRASS: 0.5,
            PokemonType.FIRE: 1.0,
            PokemonType.ELECTRIC: 0.5,
            PokemonType.NORMAL: 1.0
        },
        PokemonType.NORMAL: {
            PokemonType.FIRE: 1.0,
            PokemonType.WATER: 1.0,
            PokemonType.GRASS: 1.0,
            PokemonType.ELECTRIC: 1.0,
            PokemonType.NORMAL: 1.0
        }
    }
    
    @classmethod
    def get_multiplier(cls, attacking_type: PokemonType, defending_type: PokemonType) -> float:
        return cls.CHART[attacking_type][defending_type]

class PokemonGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pokemon Combat Simulator")
        self.root.geometry("800x1000")
        self.root.configure(bg="#2C3E50")
        
        # Game state
        self.player_pokemon = None
        self.enemy_pokemon = None
        self.battle_active = False
        self.player_turn = True
        
        # Create Pokemon roster
        self.pokemon_roster = self._create_pokemon_roster()
        
        # Type colors for visual feedback
        self.type_colors = {
            PokemonType.FIRE: "#FF6B35",
            PokemonType.WATER: "#4A90E2",
            PokemonType.GRASS: "#7ED321",
            PokemonType.ELECTRIC: "#F5A623",
            PokemonType.NORMAL: "#9B9B9B"
        }
        
        self.setup_ui()
    
    def _create_pokemon_roster(self) -> List[Pokemon]:
        moves_fire = [
            Move("Ember", 40, PokemonType.FIRE),
            Move("Flamethrower", 90, PokemonType.FIRE, 0.9),
            Move("Tackle", 40, PokemonType.NORMAL),
            Move("Quick Attack", 30, PokemonType.NORMAL)
        ]
        
        moves_water = [
            Move("Water Gun", 40, PokemonType.WATER),
            Move("Hydro Pump", 110, PokemonType.WATER, 0.8),
            Move("Tackle", 40, PokemonType.NORMAL),
            Move("Bite", 60, PokemonType.NORMAL)
        ]
        
        moves_grass = [
            Move("Vine Whip", 45, PokemonType.GRASS),
            Move("Solar Beam", 120, PokemonType.GRASS, 0.85),
            Move("Tackle", 40, PokemonType.NORMAL),
            Move("Sleep Powder", 0, PokemonType.GRASS, 0.75)
        ]
        
        moves_electric = [
            Move("Thunder Shock", 40, PokemonType.ELECTRIC),
            Move("Thunderbolt", 90, PokemonType.ELECTRIC, 0.9),
            Move("Quick Attack", 30, PokemonType.NORMAL),
            Move("Thunder Wave", 0, PokemonType.ELECTRIC, 0.9)
        ]
        
        moves_normal = [
            Move("Tackle", 40, PokemonType.NORMAL),
            Move("Hyper Beam", 150, PokemonType.NORMAL, 0.9),
            Move("Quick Attack", 30, PokemonType.NORMAL),
            Move("Body Slam", 85, PokemonType.NORMAL, 0.85)
        ]
        
        return [
            Pokemon("Charmander", PokemonType.FIRE, 100, 85, 70, 90, moves_fire),
            Pokemon("Squirtle", PokemonType.WATER, 110, 75, 85, 70, moves_water),
            Pokemon("Bulbasaur", PokemonType.GRASS, 105, 80, 80, 75, moves_grass),
            Pokemon("Pikachu", PokemonType.ELECTRIC, 90, 90, 60, 110, moves_electric),
            Pokemon("Eevee", PokemonType.NORMAL, 95, 75, 75, 85, moves_normal)
        ]
    
    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg="#2C3E50")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="Pokemon Combat Simulator", 
                              font=("Arial", 24, "bold"), 
                              fg="#ECF0F1", bg="#2C3E50")
        title_label.pack(pady=(0, 20))
        
        # Battle area (top half)
        self.battle_frame = tk.Frame(main_frame, bg="#34495E", relief=tk.RAISED, bd=2)
        self.battle_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.setup_battle_area()
        
        # Control area (bottom half)
        self.control_frame = tk.Frame(main_frame, bg="#34495E", relief=tk.RAISED, bd=2)
        self.control_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.setup_control_area()
        
        # Battle log
        self.setup_battle_log()
    
    def setup_battle_area(self):
        # Pokemon display area
        pokemon_display_frame = tk.Frame(self.battle_frame, bg="#34495E")
        pokemon_display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Player Pokemon (left side)
        self.player_frame = tk.Frame(pokemon_display_frame, bg="#2C3E50", relief=tk.RAISED, bd=2)
        self.player_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        tk.Label(self.player_frame, text="Your Pokemon", 
                font=("Arial", 14, "bold"), fg="#ECF0F1", bg="#2C3E50").pack(pady=5)
        
        # Player sprite placeholder
        self.player_sprite_frame = tk.Frame(self.player_frame, bg="#7F8C8D", width=150, height=150)
        self.player_sprite_frame.pack(pady=10)
        self.player_sprite_frame.pack_propagate(False)
        
        self.player_sprite_label = tk.Label(self.player_sprite_frame, text="[SPRITE]", 
                                           font=("Arial", 12), fg="#2C3E50", bg="#7F8C8D")
        self.player_sprite_label.pack(expand=True)
        
        # Player info
        self.player_info_frame = tk.Frame(self.player_frame, bg="#2C3E50")
        self.player_info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.player_name_label = tk.Label(self.player_info_frame, text="Select Pokemon", 
                                         font=("Arial", 12, "bold"), fg="#ECF0F1", bg="#2C3E50")
        self.player_name_label.pack()
        
        self.player_hp_label = tk.Label(self.player_info_frame, text="HP: -/-", 
                                       font=("Arial", 10), fg="#ECF0F1", bg="#2C3E50")
        self.player_hp_label.pack()
        
        # Player HP bar
        self.player_hp_frame = tk.Frame(self.player_info_frame, bg="#2C3E50")
        self.player_hp_frame.pack(fill=tk.X, pady=5)
        
        self.player_hp_bar = ttk.Progressbar(self.player_hp_frame, length=200, mode='determinate')
        self.player_hp_bar.pack()
        
        # VS Label
        vs_label = tk.Label(pokemon_display_frame, text="VS", 
                           font=("Arial", 20, "bold"), fg="#E74C3C", bg="#34495E")
        vs_label.pack(side=tk.LEFT, padx=20)
        
        # Enemy Pokemon (right side)
        self.enemy_frame = tk.Frame(pokemon_display_frame, bg="#2C3E50", relief=tk.RAISED, bd=2)
        self.enemy_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        tk.Label(self.enemy_frame, text="Enemy Pokemon", 
                font=("Arial", 14, "bold"), fg="#ECF0F1", bg="#2C3E50").pack(pady=5)
        
        # Enemy sprite placeholder
        self.enemy_sprite_frame = tk.Frame(self.enemy_frame, bg="#7F8C8D", width=150, height=150)
        self.enemy_sprite_frame.pack(pady=10)
        self.enemy_sprite_frame.pack_propagate(False)
        
        self.enemy_sprite_label = tk.Label(self.enemy_sprite_frame, text="[SPRITE]", 
                                          font=("Arial", 12), fg="#2C3E50", bg="#7F8C8D")
        self.enemy_sprite_label.pack(expand=True)
        
        # Enemy info
        self.enemy_info_frame = tk.Frame(self.enemy_frame, bg="#2C3E50")
        self.enemy_info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.enemy_name_label = tk.Label(self.enemy_info_frame, text="???", 
                                        font=("Arial", 12, "bold"), fg="#ECF0F1", bg="#2C3E50")
        self.enemy_name_label.pack()
        
        self.enemy_hp_label = tk.Label(self.enemy_info_frame, text="HP: -/-", 
                                      font=("Arial", 10), fg="#ECF0F1", bg="#2C3E50")
        self.enemy_hp_label.pack()
        
        # Enemy HP bar
        self.enemy_hp_frame = tk.Frame(self.enemy_info_frame, bg="#2C3E50")
        self.enemy_hp_frame.pack(fill=tk.X, pady=5)
        
        self.enemy_hp_bar = ttk.Progressbar(self.enemy_hp_frame, length=200, mode='determinate')
        self.enemy_hp_bar.pack()
    
    def setup_control_area(self):
        # Pokemon selection area
        self.selection_frame = tk.Frame(self.control_frame, bg="#34495E")
        self.selection_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(self.selection_frame, text="Choose Your Pokemon:", 
                font=("Arial", 12, "bold"), fg="#ECF0F1", bg="#34495E").pack(anchor=tk.W)
        
        # Pokemon selection buttons
        self.pokemon_buttons_frame = tk.Frame(self.selection_frame, bg="#34495E")
        self.pokemon_buttons_frame.pack(fill=tk.X, pady=5)
        
        self.pokemon_buttons = []
        for i, pokemon in enumerate(self.pokemon_roster):
            color = self.type_colors[pokemon.type]
            btn = tk.Button(self.pokemon_buttons_frame, text=f"{pokemon.name}\n({pokemon.type.value})", 
                           font=("Arial", 9), bg=color, fg="white", 
                           command=lambda p=pokemon: self.select_pokemon(p),
                           width=12, height=3)
            btn.pack(side=tk.LEFT, padx=2)
            self.pokemon_buttons.append(btn)
        
        # Battle controls
        self.battle_controls_frame = tk.Frame(self.control_frame, bg="#34495E")
        self.battle_controls_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.start_battle_btn = tk.Button(self.battle_controls_frame, text="Start Battle!", 
                                         font=("Arial", 14, "bold"), bg="#27AE60", fg="white",
                                         command=self.start_battle, state=tk.DISABLED)
        self.start_battle_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.new_battle_btn = tk.Button(self.battle_controls_frame, text="New Battle", 
                                       font=("Arial", 12), bg="#3498DB", fg="white",
                                       command=self.new_battle)
        self.new_battle_btn.pack(side=tk.LEFT)
        
        # Move buttons (hidden initially)
        self.moves_frame = tk.Frame(self.control_frame, bg="#34495E")
        self.moves_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.move_buttons = []
        for i in range(4):
            btn = tk.Button(self.moves_frame, text="", font=("Arial", 10), 
                           width=20, height=2, state=tk.DISABLED)
            btn.pack(side=tk.LEFT, padx=2)
            self.move_buttons.append(btn)
    
    def setup_battle_log(self):
        # Battle log area
        log_frame = tk.Frame(self.control_frame, bg="#34495E")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        tk.Label(log_frame, text="Battle Log:", 
                font=("Arial", 12, "bold"), fg="#ECF0F1", bg="#34495E").pack(anchor=tk.W)
        
        # Scrollable text area
        log_container = tk.Frame(log_frame, bg="#34495E")
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.battle_log = tk.Text(log_container, height=8, bg="#2C3E50", fg="#ECF0F1", 
                                 font=("Courier", 9), state=tk.DISABLED, wrap=tk.WORD)
        
        scrollbar = tk.Scrollbar(log_container, orient=tk.VERTICAL, command=self.battle_log.yview)
        self.battle_log.configure(yscrollcommand=scrollbar.set)
        
        self.battle_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def log_message(self, message: str):
        self.battle_log.config(state=tk.NORMAL)
        self.battle_log.insert(tk.END, message + "\n")
        self.battle_log.see(tk.END)
        self.battle_log.config(state=tk.DISABLED)
    
    def select_pokemon(self, pokemon: Pokemon):
        # Create a copy of the selected Pokemon
        self.player_pokemon = Pokemon(pokemon.name, pokemon.type, pokemon.max_hp, 
                                    pokemon.attack, pokemon.defense, pokemon.speed, 
                                    pokemon.moves.copy())
        
        # Update UI
        self.player_name_label.config(text=f"{self.player_pokemon.name} ({self.player_pokemon.type.value})")
        self.player_sprite_label.config(text=f"[{self.player_pokemon.name.upper()}]")
        self.update_hp_display()
        
        # Enable start battle button
        self.start_battle_btn.config(state=tk.NORMAL)
        
        self.log_message(f"You selected {self.player_pokemon.name}!")
    
    def start_battle(self):
        if not self.player_pokemon:
            return
        
        # Select enemy Pokemon (random)
        enemy_template = random.choice(self.pokemon_roster)
        self.enemy_pokemon = Pokemon(enemy_template.name, enemy_template.type, enemy_template.max_hp, 
                                   enemy_template.attack, enemy_template.defense, enemy_template.speed, 
                                   enemy_template.moves.copy())
        
        # Update enemy UI
        self.enemy_name_label.config(text=f"{self.enemy_pokemon.name} ({self.enemy_pokemon.type.value})")
        self.enemy_sprite_label.config(text=f"[{self.enemy_pokemon.name.upper()}]")
        
        # Start battle
        self.battle_active = True
        self.player_turn = self.player_pokemon.speed >= self.enemy_pokemon.speed
        
        # Update UI
        self.update_hp_display()
        self.update_move_buttons()
        self.start_battle_btn.config(state=tk.DISABLED)
        
        # Disable Pokemon selection
        for btn in self.pokemon_buttons:
            btn.config(state=tk.DISABLED)
        
        self.log_message(f"Battle begins! {self.player_pokemon.name} vs {self.enemy_pokemon.name}!")
        self.log_message(f"Speed check: {self.player_pokemon.name} ({self.player_pokemon.speed}) vs {self.enemy_pokemon.name} ({self.enemy_pokemon.speed})")
        
        if self.player_turn:
            self.log_message("You go first!")
        else:
            self.log_message("Enemy goes first!")
            self.root.after(1500, self.ai_turn)
    
    def update_hp_display(self):
        if self.player_pokemon:
            self.player_hp_label.config(text=f"HP: {self.player_pokemon.current_hp}/{self.player_pokemon.max_hp}")
            self.player_hp_bar['value'] = self.player_pokemon.get_hp_percentage()
        
        if self.enemy_pokemon:
            self.enemy_hp_label.config(text=f"HP: {self.enemy_pokemon.current_hp}/{self.enemy_pokemon.max_hp}")
            self.enemy_hp_bar['value'] = self.enemy_pokemon.get_hp_percentage()
    
    def update_move_buttons(self):
        if not self.battle_active or not self.player_turn or not self.player_pokemon:
            for btn in self.move_buttons:
                btn.config(state=tk.DISABLED)
            return
        
        for i, move in enumerate(self.player_pokemon.moves):
            color = self.type_colors[move.type]
            self.move_buttons[i].config(
                text=f"{move.name}\n{move.type.value} | Power: {move.power}",
                bg=color, fg="white", state=tk.NORMAL,
                command=lambda m=move: self.use_move(m)
            )
    
    def use_move(self, move: Move):
        if not self.battle_active or not self.player_turn:
            return
        
        # Disable move buttons
        for btn in self.move_buttons:
            btn.config(state=tk.DISABLED)
        
        # Execute move
        self.execute_move(self.player_pokemon, self.enemy_pokemon, move, is_player=True)
        
        # Check if enemy is defeated
        if not self.enemy_pokemon.is_alive():
            self.end_battle(player_won=True)
            return
        
        # Switch to AI turn
        self.player_turn = False
        self.root.after(1500, self.ai_turn)
    
    def ai_turn(self):
        if not self.battle_active or self.player_turn:
            return
        
        # Simple AI: prefer super effective moves
        best_moves = []
        best_effectiveness = 0
        
        for move in self.enemy_pokemon.moves:
            if move.power > 0:
                effectiveness = TypeEffectiveness.get_multiplier(move.type, self.player_pokemon.type)
                if effectiveness > best_effectiveness:
                    best_effectiveness = effectiveness
                    best_moves = [move]
                elif effectiveness == best_effectiveness:
                    best_moves.append(move)
        
        if not best_moves:
            best_moves = [move for move in self.enemy_pokemon.moves if move.power > 0]
        
        selected_move = random.choice(best_moves) if best_moves else random.choice(self.enemy_pokemon.moves)
        
        # Execute AI move
        self.execute_move(self.enemy_pokemon, self.player_pokemon, selected_move, is_player=False)
        
        # Check if player is defeated
        if not self.player_pokemon.is_alive():
            self.end_battle(player_won=False)
            return
        
        # Switch back to player turn
        self.player_turn = True
        self.update_move_buttons()
        
    def execute_move(self, attacker: Pokemon, defender: Pokemon, move: Move, is_player: bool):
        damage = self.calculate_damage(attacker, defender, move)
        
        attacker_name = attacker.name if is_player else f"Enemy {attacker.name}"
        
        if damage == 0 and move.power > 0:
            self.log_message(f"{attacker_name} uses {move.name}!")
            self.log_message(f"{move.name} missed!")
            return
        elif damage == 0:
            self.log_message(f"{attacker_name} uses {move.name}!")
            self.log_message(f"{move.name} had no effect!")
            return
        
        defender.take_damage(damage)
        
        # Get type effectiveness for message
        effectiveness = TypeEffectiveness.get_multiplier(move.type, defender.type)
        
        self.log_message(f"{attacker_name} uses {move.name}!")
        self.log_message(f"{defender.name} takes {damage} damage!")
        
        if effectiveness > 1.0:
            self.log_message("It's super effective!")
        elif effectiveness < 1.0:
            self.log_message("It's not very effective...")
        
        self.update_hp_display()
    
    def calculate_damage(self, attacker: Pokemon, defender: Pokemon, move: Move) -> int:
        if move.power == 0:
            return 0
        
        if random.random() > move.accuracy:
            return 0
        
        base_damage = ((2 * 50 + 10) / 250) * (attacker.attack / defender.defense) * move.power + 2
        type_multiplier = TypeEffectiveness.get_multiplier(move.type, defender.type)
        random_factor = random.uniform(0.85, 1.0)
        stab = 1.5 if move.type == attacker.type else 1.0
        
        final_damage = int(base_damage * type_multiplier * random_factor * stab)
        return max(1, final_damage)
    
    def end_battle(self, player_won: bool):
        self.battle_active = False
        
        # Disable move buttons
        for btn in self.move_buttons:
            btn.config(state=tk.DISABLED)
        
        if player_won:
            self.log_message(f"🎉 {self.player_pokemon.name} wins!")
            messagebox.showinfo("Victory!", f"Congratulations! Your {self.player_pokemon.name} won!")
        else:
            self.log_message(f"💀 {self.player_pokemon.name} fainted!")
            messagebox.showinfo("Defeat!", f"Your {self.player_pokemon.name} was defeated!")
        
        # Enable new battle
        self.start_battle_btn.config(state=tk.NORMAL, text="Battle Again!")
    
    def new_battle(self):
        # Reset game state
        self.player_pokemon = None
        self.enemy_pokemon = None
        self.battle_active = False
        self.player_turn = True
        
        # Reset UI
        self.player_name_label.config(text="Select Pokemon")
        self.player_hp_label.config(text="HP: -/-")
        self.player_hp_bar['value'] = 0
        self.player_sprite_label.config(text="[SPRITE]")
        
        self.enemy_name_label.config(text="???")
        self.enemy_hp_label.config(text="HP: -/-")
        self.enemy_hp_bar['value'] = 0
        self.enemy_sprite_label.config(text="[SPRITE]")
        
        # Enable Pokemon selection
        for btn in self.pokemon_buttons:
            btn.config(state=tk.NORMAL)
        
        # Reset buttons
        self.start_battle_btn.config(state=tk.DISABLED, text="Start Battle!")
        for btn in self.move_buttons:
            btn.config(state=tk.DISABLED, text="")
        
        # Clear battle log
        self.battle_log.config(state=tk.NORMAL)
        self.battle_log.delete(1.0, tk.END)
        self.battle_log.config(state=tk.DISABLED)
        
        self.log_message("Ready for a new battle!")

def main():
    root = tk.Tk()
    app = PokemonGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()