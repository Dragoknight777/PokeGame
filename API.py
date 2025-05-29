# main.py - FastAPI server
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import random

# Import our models (assuming they're in models.py)
from models import (
    Player, Area, PlayerPokemon, Trainer, Battle,
    get_db, create_tables, insert_sample_data, PokemonService
)

# Pydantic models for API requests/responses
from pydantic import BaseModel

class PlayerCreate(BaseModel):
    username: str

class PlayerResponse(BaseModel):
    id: int
    username: str
    current_area_id: int
    level: int
    experience: int
    money: int
    inventory: Dict
    
    class Config:
        from_attributes = True

class AreaResponse(BaseModel):
    id: int
    name: str
    description: str
    level_range: str
    
    class Config:
        from_attributes = True

class PokemonEncounterResponse(BaseModel):
    pokemon_id: int
    name: str
    level: int
    types: List[str]
    stats: Dict
    moves: List[str]
    sprite: str
    current_hp: int

class BattleAction(BaseModel):
    action: str  # "attack", "catch", "run"
    move_name: Optional[str] = None

# Initialize FastAPI app
app = FastAPI(title="Pokemon Roguelike API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    create_tables()
    insert_sample_data()

# API Endpoints

@app.post("/players/", response_model=PlayerResponse)
def create_player(player: PlayerCreate, db: Session = Depends(get_db)):
    """Create a new player"""
    # Check if username already exists
    existing_player = db.query(Player).filter(Player.username == player.username).first()
    if existing_player:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create new player with starter pokemon
    new_player = Player(
        username=player.username,
        current_area_id=1,
        inventory={"pokeball": 5, "potion": 3, "antidote": 2}
    )
    
    db.add(new_player)
    db.commit()
    db.refresh(new_player)
    
    # Give starter pokemon (Charmander)
    starter_data = PokemonService.get_pokemon_data(4)  # Charmander
    if starter_data:
        starter_stats = PokemonService.calculate_stats(starter_data["stats"], 5)
        starter_pokemon = PlayerPokemon(
            owner_id=new_player.id,
            pokemon_id=4,
            nickname="Charmander",
            level=5,
            current_hp=starter_stats["hp"],
            max_hp=starter_stats["hp"],
            attack=starter_stats["attack"],
            defense=starter_stats["defense"],
            speed=starter_stats["speed"],
            moves=starter_data["moves"][:4],
            is_in_party=True
        )
        db.add(starter_pokemon)
        db.commit()
    
    return new_player

@app.get("/players/{player_id}", response_model=PlayerResponse)
def get_player(player_id: int, db: Session = Depends(get_db)):
    """Get player information"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@app.get("/areas/", response_model=List[AreaResponse])
def get_areas(db: Session = Depends(get_db)):
    """Get all available areas"""
    areas = db.query(Area).all()
    return areas

@app.get("/areas/{area_id}", response_model=AreaResponse)
def get_area(area_id: int, db: Session = Depends(get_db)):
    """Get specific area information"""
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    return area

@app.post("/players/{player_id}/move/{area_id}")
def move_player(player_id: int, area_id: int, db: Session = Depends(get_db)):
    """Move player to a different area"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    
    # Check if area is unlocked (simplified logic)
    if not area.is_unlocked_by_default and area.required_areas_completed:
        # In a full implementation, you'd check if required areas are completed
        pass
    
    player.current_area_id = area_id
    db.commit()
    
    return {"message": f"Moved to {area.name}", "current_area_id": area_id}

@app.post("/players/{player_id}/encounter", response_model=PokemonEncounterResponse)
def wild_pokemon_encounter(player_id: int, db: Session = Depends(get_db)):
    """Generate a wild pokemon encounter in the player's current area"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    area = db.query(Area).filter(Area.id == player.current_area_id).first()
    if not area or not area.wild_pokemon_data:
        raise HTTPException(status_code=400, detail="No wild pokemon in this area")
    
    # Generate wild pokemon encounter
    wild_pokemon = PokemonService.generate_wild_pokemon(area.wild_pokemon_data, player.level)
    if not wild_pokemon:
        raise HTTPException(status_code=500, detail="Failed to generate wild pokemon")
    
    return wild_pokemon

@app.get("/players/{player_id}/pokemon")
def get_player_pokemon(player_id: int, db: Session = Depends(get_db)):
    """Get all pokemon owned by the player"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    pokemon = db.query(PlayerPokemon).filter(PlayerPokemon.owner_id == player_id).all()
    
    result = []
    for p in pokemon:
        base_data = PokemonService.get_pokemon_data(p.pokemon_id)
        result.append({
            "id": p.id,
            "pokemon_id": p.pokemon_id,
            "name": base_data["name"] if base_data else "Unknown",
            "nickname": p.nickname,
            "level": p.level,
            "current_hp": p.current_hp,
            "max_hp": p.max_hp,
            "is_in_party": p.is_in_party,
            "sprite": base_data["sprite"] if base_data else None
        })
    
    return result

@app.get("/areas/{area_id}/trainers")
def get_area_trainers(area_id: int, db: Session = Depends(get_db)):
    """Get all trainers in an area"""
    trainers = db.query(Trainer).filter(Trainer.area_id == area_id).all()
    
    result = []
    for trainer in trainers:
        result.append({
            "id": trainer.id,
            "name": trainer.name,
            "is_gym_leader": trainer.is_gym_leader,
            "pokemon_team": trainer.pokemon_team,
            "reward_money": trainer.reward_money
        })
    
    return result

@app.post("/players/{player_id}/catch/{pokemon_id}")
def catch_pokemon(player_id: int, pokemon_id: int, level: int = 5, db: Session = Depends(get_db)):
    """Catch a wild pokemon (simplified - normally would be part of battle system)"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Check if player has pokeballs
    if player.inventory.get("pokeball", 0) <= 0:
        raise HTTPException(status_code=400, detail="No pokeballs available")
    
    # Get pokemon data
    pokemon_data = PokemonService.get_pokemon_data(pokemon_id)
    if not pokemon_data:
        raise HTTPException(status_code=400, detail="Invalid pokemon ID")
    
    # Calculate stats for the caught pokemon
    stats = PokemonService.calculate_stats(pokemon_data["stats"], level)
    
    # Create new pokemon for player
    new_pokemon = PlayerPokemon(
        owner_id=player_id,
        pokemon_id=pokemon_id,
        nickname=pokemon_data["name"].capitalize(),
        level=level,
        current_hp=stats["hp"],
        max_hp=stats["hp"],
        attack=stats["attack"],
        defense=stats["defense"],
        speed=stats["speed"],
        moves=pokemon_data["moves"][:4]
    )
    
    # Reduce pokeball count
    player.inventory["pokeball"] -= 1
    
    db.add(new_pokemon)
    db.commit()
    
    return {
        "message": f"Successfully caught {pokemon_data['name']}!",
        "pokemon": {
            "name": pokemon_data["name"],
            "level": level,
            "sprite": pokemon_data["sprite"]
        }
    }

# Health check endpoint
@app.get("/")
def root():
    return {"message": "Pokemon Roguelike API is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)