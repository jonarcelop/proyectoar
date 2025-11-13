/**
 * Single-Player Game Manager (vs IA)
 * Maneja juegos contra la IA Minimax
 */

class SinglePlayerGame {
    constructor() {
        this.gameId = null;
        this.board = [];
        this.wins = { X: 0, O: 0 };
        this.difficulty = "hard";
        this.isGameActive = false;
        this.waitingForAI = false;
    }

    /**
     * Inicia un nuevo juego single-player
     */
    async startGame(difficulty = "hard") {
        this.difficulty = difficulty;
        
        try {
            const response = await fetch("/api/single-player/game", {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });
            
            if (!response.ok) {
                throw new Error("Error creando juego");
            }
            
            const data = await response.json();
            this.gameId = data.gameId;
            this.board = data.board;
            this.wins = data.wins;
            this.isGameActive = true;
            this.waitingForAI = false;
            
            console.log("Single-player game iniciado:", this.gameId);
            return { success: true, data };
        } catch (error) {
            console.error("Error en startGame:", error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Realiza un movimiento en el juego
     */
    async makeMove(row, col) {
        if (!this.gameId || this.waitingForAI) {
            console.warn("No puedes mover en este momento");
            return { success: false, error: "Esperando IA..." };
        }

        this.waitingForAI = true;

        try {
            const response = await fetch(`/api/single-player/${this.gameId}/move`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ position: [row, col] })
            });

            const data = await response.json();

            if (!response.ok) {
                this.waitingForAI = false;
                return { success: false, error: data.message || "Error en movimiento" };
            }

            // Actualizar estado
            this.board = data.board;
            if (data.wins) this.wins = data.wins;

            // Verificar fin del juego
            if (data.winner) {
                this.isGameActive = false;
                this.waitingForAI = false;
                console.log("Ganador:", data.winner);
                return { success: true, result: "win", winner: data.winner, data };
            }

            if (data.draw) {
                this.isGameActive = false;
                this.waitingForAI = false;
                console.log("Empate!");
                return { success: true, result: "draw", data };
            }

            // IA respondió
            this.waitingForAI = false;
            return { success: true, result: "move", data };
        } catch (error) {
            console.error("Error en makeMove:", error);
            this.waitingForAI = false;
            return { success: false, error: error.message };
        }
    }

    /**
     * Reinicia la ronda actual
     */
    async resetRound() {
        if (!this.gameId) {
            return { success: false, error: "No hay juego activo" };
        }

        try {
            const response = await fetch(`/api/single-player/${this.gameId}/reset`, {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });

            const data = await response.json();

            if (!response.ok) {
                return { success: false, error: data.message };
            }

            this.board = data.board;
            this.wins = data.wins;
            this.isGameActive = true;
            this.waitingForAI = false;

            return { success: true, data };
        } catch (error) {
            console.error("Error en resetRound:", error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Reinicia todo el match (contador de wins)
     */
    async resetMatch() {
        if (!this.gameId) {
            return { success: false, error: "No hay juego activo" };
        }

        try {
            const response = await fetch(`/api/single-player/${this.gameId}/reset-match`, {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });

            const data = await response.json();

            if (!response.ok) {
                return { success: false, error: data.message };
            }

            this.board = data.board;
            this.wins = data.wins;
            this.isGameActive = true;
            this.waitingForAI = false;

            return { success: true, data };
        } catch (error) {
            console.error("Error en resetMatch:", error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Obtiene estado actual del tablero
     */
    getBoard() {
        return this.board;
    }

    /**
     * Obtiene el contador de wins
     */
    getWins() {
        return this.wins;
    }

    /**
     * Verifica si el juego está activo
     */
    isActive() {
        return this.isGameActive;
    }
}

// Instancia global
const spGame = new SinglePlayerGame();
