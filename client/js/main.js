// ===== Game State =====
let gameMode = "multiplayer"; // "multiplayer" o "singleplayer"
let gameId = null;
let playerId = null;
let symbol = null;
let board = null;
let myTurn = false;

// ===== Utility function =====
function $(id) {
    return document.getElementById(id);
}

function log(msg) {
    const logDiv = $("log");
    const p = document.createElement("p");
    p.innerText = msg;
    logDiv.appendChild(p);
    logDiv.scrollTop = logDiv.scrollHeight;
}

// ===== Mode Selection =====
$("modeMultiplayer").onclick = () => switchMode("multiplayer");
$("modeSinglePlayer").onclick = () => switchMode("singleplayer");

function switchMode(mode) {
    gameMode = mode;
    
    // Actualizar botones
    $("modeMultiplayer").classList.toggle("active", mode === "multiplayer");
    $("modeSinglePlayer").classList.toggle("active", mode === "singleplayer");
    
    // Actualizar cajas
    $("multiplayerBox").classList.toggle("hidden", mode !== "multiplayer");
    $("singlePlayerBox").classList.toggle("hidden", mode !== "singleplayer");
    
    // Ocultar juego
    $("gameContainer").classList.add("hidden");
    
    // Limpiar estado
    if (mode === "multiplayer" && ws) {
        // Reconectar si es necesario
    }
    
    log(`Modo cambiado a: ${mode === "multiplayer" ? "Multijugador" : "Single-Player"}`);
}

// ===== Multiplayer =====
$("connectBtn").onclick = () => connectWS("join");
$("resumeBtn").onclick = () => connectWS("resume");
$("resetMatchBtn").onclick = () => sendResetMatchAndHide();
$("sendChatBtn").onclick = () => sendChatMessage();

// Chat: enviar mensaje al presionar Enter
$("chatInput").onkeypress = (e) => {
    if (e.key === "Enter") sendChatMessage();
};

function sendChatMessage() {
    const input = $("chatInput");
    const message = input.value.trim();
    
    if (!message) return;
    if (!gameId) return alert("No estás en una partida");
    
    if (gameMode === "multiplayer" && ws) {
        ws.send(JSON.stringify({
            type: "chat_message",
            message: message,
            gameId: gameId
        }));
    } else if (gameMode === "singleplayer") {
        // Single-player: solo mostrar mensaje localmente (sin servidor de chat)
        addChatMessage("Tú", message);
    }
    
    input.value = "";
}

function addChatMessage(sender, text) {
    const chatBox = $("chatBox");
    const msgDiv = document.createElement("div");
    msgDiv.className = "chat-message";
    msgDiv.innerHTML = `<div class="chat-message-sender">${sender}:</div><div class="chat-message-text">${text}</div>`;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function handleWSMessage(msg) {
    if (msg.type === "registered") {
        playerId = msg.playerId;
        $("playerId").value = playerId;
        log("Registrado playerId: " + playerId);
        return;
    }

    if (msg.type === "waiting") {
        log("Esperando rival...");
        $("status").innerText = "Esperando rival…";
        return;
    }

    if (msg.type === "assigned") {
        symbol = msg.symbol;
        gameId = msg.gameId;
        log("Asignado: eres " + symbol);
        $("gameContainer").classList.remove("hidden");
        $("chatSection").classList.remove("hidden");
        $("status").innerText = `Partida ${gameId} - Eres ${symbol}`;
        $("chatBox").innerHTML = "";
        return;
    }

    if (msg.type === "state") {
        board = msg.board;
        myTurn = (msg.turn === symbol);
        renderBoard(board, sendMove);

        if (myTurn) unblockBoard();
        else blockBoard();

        $("turnInfo").innerText = `Turno: ${msg.turn}`;
        $("gameMessage").innerText = `Ganadas: X=${msg.wins.X} O=${msg.wins.O}`;
        const btn = $("resetMatchBtn");
        if (btn) btn.classList.add("hidden");
        return;
    }

    if (msg.type === "chat_message") {
        addChatMessage(msg.sender, msg.message);
        return;
    }

    if (msg.type === "timeout") {
        log("Timeout: " + msg.message);
        $("turnInfo").innerText = msg.message;
        return;
    }

    if (msg.type === "win") {
        log("Ganador de la ronda: " + msg.winner);
        $("gameMessage").innerText = `Ganador de la ronda: ${msg.winner}`;

        renderBoard([["-","-","-"],["-","-","-"],["-","-","-"]], sendMove);
        blockBoard();

        if (msg.matchFinished) {
            $("turnInfo").innerText = "¡El match ha terminado!";
            log("Partida finalizada. Ganador final: " + msg.winner);
            $("resetMatchBtn").classList.remove("hidden");
            blockBoard();
        }
        return;
    }

    if (msg.type === "draw") {
        log("Empate en la ronda");
        $("gameMessage").innerText = "Ronda empatada";

        renderBoard([["-","-","-"],["-","-","-"],["-","-","-"]], sendMove);
        blockBoard();
        $("resetMatchBtn").classList.remove("hidden");
        return;
    }

    if (msg.type === "opponentDisconnected") {
        log("El rival se ha desconectado");
        $("gameMessage").innerText = "Rival desconectado";
        blockBoard();
        return;
    }

    if (msg.type === "error") {
        const message = msg.message || "Error desconocido";
        alert(message);
        log("ERROR [" + (msg.code || "unknown") + "]: " + message);
        return;
    }

    log("Mensaje desconocido: " + JSON.stringify(msg));
}

// ===== Single-Player =====
$("startSinglePlayerBtn").onclick = async () => {
    console.log("🎮 Single-Player button clicked!");
    const difficulty = $("difficultySelect").value;
    console.log("📊 Difficulty:", difficulty);
    $("startSinglePlayerBtn").disabled = true;
    $("spStatus").innerText = "Iniciando...";
    
    console.log("🔄 Llamando spGame.startGame()...");
    const result = await spGame.startGame(difficulty);
    console.log("✅ Resultado:", result);
    
    if (result.success) {
        gameMode = "singleplayer";
        gameId = spGame.gameId;
        symbol = "X";
        
        log(`Juego single-player iniciado (${difficulty})`);
        $("spStatus").innerText = "¡Juego iniciado! Eres X (empiezas tú)";
        
        // Mostrar juego
        $("gameContainer").classList.remove("hidden");
        $("chatSection").classList.add("hidden"); // Sin chat en single-player
        
        // Renderizar tablero
        const board = spGame.getBoard();
        renderBoard(board, sendMoveSinglePlayer);
        unblockBoard();
        
        $("turnInfo").innerText = "Tu turno (X)";
        updateWinsSinglePlayer();
    } else {
        $("spStatus").innerText = "Error: " + result.error;
        $("startSinglePlayerBtn").disabled = false;
    }
};

async function sendMoveSinglePlayer(row, col) {
    if (gameMode !== "singleplayer") return;
    
    blockBoard();
    $("turnInfo").innerText = "IA pensando...";
    
    const result = await spGame.makeMove(row, col);
    
    if (!result.success) {
        $("gameMessage").innerText = result.error;
        unblockBoard();
        $("turnInfo").innerText = "Tu turno (X)";
        return;
    }
    
    // Renderizar nuevo estado
    const board = spGame.getBoard();
    renderBoard(board, sendMoveSinglePlayer);
    updateWinsSinglePlayer();
    
    if (result.result === "win") {
        const winner = result.winner;
        log(`Ganador: ${winner}`);
        $("gameMessage").innerText = `Ganador: ${winner}`;
        $("turnInfo").innerText = winner === "X" ? "¡Ganaste!" : "Perdiste...";
        
        if (!result.data.matchFinished) {
            // Mostrar botón reset después de un delay
            setTimeout(() => {
                $("resetMatchBtn").classList.remove("hidden");
                $("resetMatchBtn").onclick = async () => {
                    const res = await spGame.resetRound();
                    if (res.success) {
                        $("resetMatchBtn").classList.add("hidden");
                        const board = spGame.getBoard();
                        renderBoard(board, sendMoveSinglePlayer);
                        updateWinsSinglePlayer();
                        unblockBoard();
                        $("turnInfo").innerText = "Tu turno (X)";
                        log("Ronda reiniciada");
                    }
                };
            }, 500);
        } else {
            $("resetMatchBtn").classList.remove("hidden");
            $("resetMatchBtn").textContent = "Reiniciar Match";
            $("resetMatchBtn").onclick = async () => {
                const res = await spGame.resetMatch();
                if (res.success) {
                    $("resetMatchBtn").classList.add("hidden");
                    $("resetMatchBtn").textContent = "Reiniciar Serie (best-of)";
                    const board = spGame.getBoard();
                    renderBoard(board, sendMoveSinglePlayer);
                    updateWinsSinglePlayer();
                    unblockBoard();
                    $("turnInfo").innerText = "Tu turno (X)";
                    log("Match reiniciado");
                }
            };
        }
        
        blockBoard();
    } else if (result.result === "draw") {
        log("Empate");
        $("gameMessage").innerText = "Ronda empatada";
        $("turnInfo").innerText = "Empate";
        
        setTimeout(() => {
            $("resetMatchBtn").classList.remove("hidden");
            $("resetMatchBtn").onclick = async () => {
                const res = await spGame.resetRound();
                if (res.success) {
                    $("resetMatchBtn").classList.add("hidden");
                    const board = spGame.getBoard();
                    renderBoard(board, sendMoveSinglePlayer);
                    updateWinsSinglePlayer();
                    unblockBoard();
                    $("turnInfo").innerText = "Tu turno (X)";
                    log("Ronda reiniciada");
                }
            };
        }, 500);
        
        blockBoard();
    } else {
        // Siguiente turno: IA ya movió
        $("turnInfo").innerText = "Tu turno (X)";
        unblockBoard();
    }
}

function updateWinsSinglePlayer() {
    const wins = spGame.getWins();
    $("gameMessage").innerText = `Ganadas: X=${wins.X} O=${wins.O}`;
}

