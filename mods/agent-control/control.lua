-- Agent Control System
-- Handles RCON commands for external agent control

-- Register console commands
commands.add_command("agent_move", "Move player: agent_move <player_name> <direction>", function(command)
    local params = {}
    for param in command.parameter:gmatch("%S+") do
        table.insert(params, param)
    end
    
    if #params < 2 then
        game.print("Usage: agent_move <player_name> <direction>")
        return
    end
    
    local player_name = params[1]
    local direction = tonumber(params[2])
    local player = game.players[player_name]
    
    if not player then
        game.print("Player not found: " .. player_name)
        return
    end
    
    if not player.character then
        game.print("Player has no character: " .. player_name)
        return
    end
    
    -- Set walking state
    player.character.walking_state = {walking = true, direction = direction}
    game.print("Moving player " .. player_name .. " in direction " .. direction)
end)

commands.add_command("agent_stop", "Stop player movement: agent_stop <player_name>", function(command)
    local player_name = command.parameter
    local player = game.players[player_name]
    
    if not player then
        game.print("Player not found: " .. player_name)
        return
    end
    
    if not player.character then
        game.print("Player has no character: " .. player_name)
        return
    end
    
    -- Stop walking
    player.character.walking_state = {walking = false}
    game.print("Stopped player " .. player_name)
end)

commands.add_command("agent_status", "Get player status: agent_status <player_name>", function(command)
    local player_name = command.parameter
    local player = game.players[player_name]
    
    if not player then
        game.print("Player not found: " .. player_name)
        return
    end
    
    if not player.character then
        game.print("Player has no character: " .. player_name)
        return
    end
    
    local pos = player.character.position
    local status = {
        name = player.name,
        position = {x = pos.x, y = pos.y},
        walking = player.character.walking_state.walking,
        direction = player.character.walking_state.direction
    }
    
    game.print("STATUS:" .. serpent.line(status))
end)

game.print("Agent Control System loaded")
