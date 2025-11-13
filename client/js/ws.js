ws = null;
playerId = null;
symbol = null;
gameId = null;
myTurn = false;
board = [["-","-","-"],["-","-","-"],["-","-","-"]];

function connectWS(type) {
    ws = new WebSocket("ws://localhost:8000/ws");

    ws.onopen = () => {
        log("Conexión abierta");
        const name = $("name").value || "Jugador";

        let payload = {
            type,
            playerName: name
        };

        if (type === "resume") {
            payload.playerId = $("playerId").value.trim();
        }

        ws.send(JSON.stringify(payload));
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        console.log(msg);
        handleWSMessage(msg);
    };

    ws.onclose = () => {
        log("Conexión cerrada");
        $("status").innerText = "Desconectado";
        blockBoard();
    };
}

function sendMove(row, col) {
    if (!myTurn) return alert("No es tu turno");
    ws.send(JSON.stringify({
        type: "move",
        position: [row, col],
        gameId
    }));
}

function sendResetMatch() {
    if (!gameId) return alert("No estás en una partida");
    ws.send(JSON.stringify({
        type: "reset_match",
        gameId
    }));
}

// Hide the reset button locally right after sending the request
// to avoid duplicate clicks while waiting for server confirmation.
function sendResetMatchAndHide() {
    sendResetMatch();
    const btn = $("resetMatchBtn");
    if (btn) btn.classList.add("hidden");
    // optimistically block the board until new state arrives
    blockBoard();
}
