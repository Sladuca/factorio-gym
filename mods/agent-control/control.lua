-- Agent Control System
-- Handles RCON commands for external agent control

-- Global functions for RCON access via /silent-command
-- These return responses via rcon.print() which works correctly with RCON

function agent_ensure_player(player_name)
    if not player_name or player_name == "" then
        rcon.print("ERROR: Usage: agent_ensure_player('player_name')")
        return
    end
    
    local player = game.players[player_name]
    
    if player then
        rcon.print("Player already exists: " .. player_name)
        return
    end
    
    -- Create a new player
    player = game.create_player(player_name)
    if player and player.character then
        -- Position the new player at spawn
        player.character.teleport({0, 0})
        rcon.print("Created player: " .. player_name)
    else
        rcon.print("Failed to create player: " .. player_name)
    end
end

function agent_move(player_name, direction)
    if not player_name or not direction then
        rcon.print("ERROR: Usage: agent_move('player_name', direction)")
        return
    end
    
    local player = game.players[player_name]
    
    if not player then
        rcon.print("Player not found: " .. player_name)
        return
    end
    
    if not player.character then
        rcon.print("Player has no character: " .. player_name)
        return
    end
    
    -- Set walking state
    player.character.walking_state = {walking = true, direction = direction}
    rcon.print("Moving player " .. player_name .. " in direction " .. direction)
end

function agent_stop(player_name)
    if not player_name then
        rcon.print("ERROR: Usage: agent_stop('player_name')")
        return
    end
    
    local player = game.players[player_name]
    
    if not player then
        rcon.print("Player not found: " .. player_name)
        return
    end
    
    if not player.character then
        rcon.print("Player has no character: " .. player_name)
        return
    end
    
    -- Stop walking
    player.character.walking_state = {walking = false}
    rcon.print("Stopped player " .. player_name)
end

function agent_status(player_name)
    if not player_name then
        rcon.print("ERROR: Usage: agent_status('player_name')")
        return
    end
    
    local player = game.players[player_name]
    
    if not player then
        rcon.print("Player not found: " .. player_name)
        return
    end
    
    if not player.character then
        rcon.print("Player has no character: " .. player_name)
        return
    end
    
    local pos = player.character.position
    local status = {
        name = player.name,
        position = {x = pos.x, y = pos.y},
        walking = player.character.walking_state.walking,
        direction = player.character.walking_state.direction
    }
    
    rcon.print("STATUS:" .. serpent.line(status))
end

-- Helper function to send responses to either RCON or player (keeping for compatibility)
local function send_response(command, message)
    if command.player_index then
        game.get_player(command.player_index).print(message)
    else
        rcon.print(message)
    end
end

-- Command to explicitly create a player if needed
commands.add_command("ensure_player", "Create player if not exists: ensure_player <player_name>", function(command)
    if not command.parameter or command.parameter == "" then
        send_response(command, "Usage: ensure_player <player_name>")
        return
    end
    
    local player_name = command.parameter:match("%S+")
    if not player_name then
        send_response(command, "Usage: ensure_player <player_name>")
        return
    end
    
    local player = game.players[player_name]
    
    if player then
        send_response(command, "Player already exists: " .. player_name)
        return
    end
    
    -- Create a new player
    player = game.create_player(player_name)
    if player and player.character then
        -- Position the new player at spawn
        player.character.teleport({0, 0})
        send_response(command, "Created player: " .. player_name)
    else
        send_response(command, "Failed to create player: " .. player_name)
    end
end)

-- Register console commands that return status via rcon.print
commands.add_command("agent_move", "Move player: agent_move <player_name> <direction>", function(command)
    if not command.parameter or command.parameter == "" then
        send_response(command, "Usage: agent_move <player_name> <direction>")
        return
    end
    
    local params = {}
    for param in command.parameter:gmatch("%S+") do
        table.insert(params, param)
    end
    
    if #params < 2 then
        send_response(command, "Usage: agent_move <player_name> <direction>")
        return
    end
    
    local player_name = params[1]
    local direction = tonumber(params[2])
    
    local player = game.players[player_name]
    
    if not player then
        send_response(command, "Player not found: " .. player_name)
        return
    end
    
    if not player.character then
        send_response(command, "Player has no character: " .. player_name)
        return
    end
    
    -- Set walking state
    player.character.walking_state = {walking = true, direction = direction}
    send_response(command, "Moving player " .. player_name .. " in direction " .. direction)
end)

commands.add_command("agent_stop", "Stop player movement: agent_stop <player_name>", function(command)
    if not command.parameter or command.parameter == "" then
        send_response(command, "Usage: agent_stop <player_name>")
        return
    end
    
    local player_name = command.parameter:match("%S+")
    local player = game.players[player_name]
    
    if not player then
        send_response(command, "Player not found: " .. player_name)
        return
    end
    
    if not player.character then
        send_response(command, "Player has no character: " .. player_name)
        return
    end
    
    -- Stop walking
    player.character.walking_state = {walking = false}
    send_response(command, "Stopped player " .. player_name)
end)

commands.add_command("agent_status", "Get player status: agent_status <player_name>", function(command)
    if not command.parameter or command.parameter == "" then
        send_response(command, "Usage: agent_status <player_name>")
        return
    end
    
    local player_name = command.parameter:match("%S+")
    local player = game.players[player_name]
    
    if not player then
        send_response(command, "Player not found: " .. player_name)
        return
    end
    
    if not player.character then
        send_response(command, "Player has no character: " .. player_name)
        return
    end
    
    local pos = player.character.position
    local status = {
        name = player.name,
        position = {x = pos.x, y = pos.y},
        walking = player.character.walking_state.walking,
        direction = player.character.walking_state.direction
    }
    
    send_response(command, "STATUS:" .. serpent.line(status))
end)

-- Debug command to test RCON  
commands.add_command("hello", "Test RCON response", function(command)
    send_response(command, "Hello from RCON!")
end)

-- Debug commands to test RCON response methods
commands.add_command("test1", "Test rcon.print response", function(command)
    rcon.print("Test1: This is from rcon.print")
end)

commands.add_command("test2", "Test game.print response", function(command)
    game.print("Test2: This is from game.print")
end)

commands.add_command("test3", "Test command structure", function(command)
    local info = "Test3: player_index=" .. tostring(command.player_index) .. 
                ", name=" .. tostring(command.name) .. 
                ", parameter=" .. tostring(command.parameter)
    rcon.print(info)
    game.print(info)  -- Also print to game for comparison
end)

-- Event handler for when the mod is loaded
script.on_init(function()
    game.print("Agent Control System loaded")
end)
