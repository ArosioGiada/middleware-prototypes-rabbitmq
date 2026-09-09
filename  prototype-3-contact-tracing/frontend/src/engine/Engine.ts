import pawn from './pawn.svg'
import grass from './grass.svg'
import type {Account} from "../app/world/World.tsx";

export default class Engine {
    private canvas: HTMLCanvasElement;
    private context: CanvasRenderingContext2D;
    private run = false;
    private requestAnimationFrame: number | null = null;

    private zoom = 50.0;
    private camera = {x: 0, y: 0};

    private account: Account;
    private position_send_interval: number | null = null;

    private direction = {x: 0, y: 0};
    private direction_keys = {
        up: false,
        down: false,
        left: false,
        right: false,
    }

    private isDragging = false;
    private lastCursorPos = {x: 0, y: 0};
    private renderDistance = 128;
    private dimensions: {w: number, h: number};

    private pawn: HTMLImageElement = new Image();
    private grass: HTMLImageElement = new Image();

    private grasses: {x: number, y: number}[];
    private accounts: Record<number, Account> = {};
    private positionEventSource: EventSource;

    constructor(
        canvas: HTMLCanvasElement,
        dimensions: {w: number, h: number},
        account: Account,
        accounts: Account[],
        onHoverChange: (account: Account | null, cursor: {
            x: number,
            y: number
        }
    ) => void ){
        const context = canvas.getContext('2d');
        if (!context) throw new Error('failed to create 2d context')
        this.dimensions = dimensions
        this.account = account
        this.context = context
        this.canvas = canvas

        this.pawn.src = pawn;
        this.grass.src = grass;

        this.accounts = Object.fromEntries(accounts.map(account => [account.account_id, account]))
        this.accounts[account.account_id] = account;
        this.camera = {...account}

        this.grasses = Array.from({ length: 256 }, () => {
            const x = Math.floor(Math.random() * (this.dimensions.w + 1));
            const y = Math.floor(Math.random() * (this.dimensions.h + 1));

            return {x, y}
        })

        window.addEventListener("resize", this.resize)

        this.positionEventSource = new EventSource(`/api/position/callback`)
        this.positionEventSource.onmessage = (event) => {
            const message: Account = JSON.parse(event.data);
            this.accounts[message.account_id] = message
        };

        this.canvas.addEventListener("wheel", (e) => {
            if (!e.ctrlKey) return;

            e.preventDefault();

            const rect = this.canvas.getBoundingClientRect();
            const cursor = {x: e.clientX - rect.left, y: e.clientY - rect.top}

            const dpr = window.devicePixelRatio || 1;

            const w = this.canvas.width;
            const h = this.canvas.height;

            const zBefore = this.zoom * dpr;
            const center = {x: w / 2, y: h / 2}

            // world position of cursor
            const world = {x: (cursor.x * dpr - center.x) / zBefore + this.camera.x, y: (cursor.y * dpr - center.y) / zBefore + this.camera.y}

            // change zoom
            const zoomFactor = 1.1;
            if (e.deltaY < 0) {
                this.zoom *= zoomFactor;
            } else {
                this.zoom /= zoomFactor;
            }

            this.zoom = Math.max(1, Math.min(this.zoom, 500));
            const zAfter = this.zoom * dpr;
            this.camera = {x: world.x - (cursor.x * dpr - center.x) / zAfter, y: world.y - (cursor.y * dpr - center.y) / zAfter}
        }, { passive: false });

        this.canvas.addEventListener("pointerdown", (e) => {
            if (e.button !== 0) return;

            this.isDragging = true;
            this.lastCursorPos = {x: e.clientX, y: e.clientY};

            this.canvas.setPointerCapture(e.pointerId)
        })

        this.canvas.addEventListener("pointermove", (e) => {
            const world = this.getWorldCursorPosition(e);

            const account = Object.values(this.accounts).find((value) =>
                value.x === Math.trunc(world.x) &&
                value.y === Math.trunc(world.y)
            )

            onHoverChange(account ?? null, {x: e.clientX, y: e.clientY})
        });

        this.canvas.addEventListener("pointermove", (e) => {
            if (!this.isDragging) return;

            const offset = {x: e.clientX - this.lastCursorPos.x, y: e.clientY - this.lastCursorPos.y};
            this.lastCursorPos = {x: e.clientX, y: e.clientY};

            this.camera.x -= offset.x / (this.zoom);
            this.camera.y -= offset.y / (this.zoom);
        })

        this.canvas.addEventListener("pointerup", (e) => {
            this.isDragging = false;

            try {
                this.canvas.releasePointerCapture(e.pointerId)
            } catch { /* empty */ }
        })

        this.canvas.addEventListener("pointerleave", (e) => {
            this.isDragging = false;

            try {
                this.canvas.releasePointerCapture(e.pointerId)
            } catch { /* empty */ }
        })

        window.addEventListener("keydown", this.handleKeyDown);
        window.addEventListener("keyup", this.handleKeyUp);

    }

    private handleKeyDown = (e: KeyboardEvent) => {
        if (e.repeat) return;

        switch (e.code) {
            case "ArrowUp":
                this.direction_keys.up = true
                break;

            case "ArrowDown":
                this.direction_keys.down = true
                break;

            case "ArrowLeft":
                this.direction_keys.left = true
                break;

            case "ArrowRight":
                this.direction_keys.right = true
                break;

            default:
                return;
        }

        if (this.position_send_interval === null) {
            this.send_position()
            this.position_send_interval = setInterval(this.send_position, 100)
        }
    }

    private handleKeyUp = (e: KeyboardEvent) => {
        switch (e.code) {
            case "ArrowUp":
                this.direction_keys.up = false
                break;

            case "ArrowDown":
                this.direction_keys.down = false
                break;

            case "ArrowLeft":
                this.direction_keys.left = false
                break;

            case "ArrowRight":
                this.direction_keys.right = false
                break;

            default:
                return;
        }

        this.clean_interval();
    }

    private clean_interval() {
        if (!this.direction_keys.up && !this.direction_keys.down && !this.direction_keys.left && !this.direction_keys.right) {
            if (this.position_send_interval !== null) {
                clearInterval(this.position_send_interval)
                this.position_send_interval = null
            }
        }
    }

    private getWorldCursorPosition(event: PointerEvent | MouseEvent) {
        const rect = this.canvas.getBoundingClientRect();

        const dpr = window.devicePixelRatio || 1;
        const z = this.zoom * dpr;

        const w = this.canvas.width;
        const h = this.canvas.height;

        const center = {
            x: w / 2,
            y: h / 2,
        };

        const screen = {
            x: (event.clientX - rect.left) * dpr,
            y: (event.clientY - rect.top) * dpr,
        };

        const world = {
            x: (screen.x - center.x) / z + this.camera.x,
            y: (screen.y - center.y) / z + this.camera.y,
        };

        return world;
    }

    start() {
        if (this.run) return;
        this.run = true

        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                this.resize()
                this.update()
            })
        })
    }

    stop() {
        this.run = false
        this.positionEventSource.close()

        window.removeEventListener('keydown', this.handleKeyDown);
        window.removeEventListener("keyup", this.handleKeyUp);

        if (this.position_send_interval !== null) {
            clearInterval(this.position_send_interval);
            this.position_send_interval = null;
        }

    }

    getCamera() {
        return {...this.camera}
    }

    getPosition(): {x: number, y: number} {
        return {...this.account}
    }

    getAccountName(account_id: number) {
        return this.accounts[account_id].account_name
    }

    private update() {
        if (this.requestAnimationFrame !== null) return;
        if (!this.run) return;
        this.draw()
        this.requestAnimationFrame = requestAnimationFrame((/*time*/) => {
            this.requestAnimationFrame = null;
            this.update();
        })
    }

    private draw() {
        const w = this.canvas.width
        const h = this.canvas.height

        this.context.setTransform(1, 0, 0, 1, 0, 0)
        this.context.clearRect(0, 0, w, h)

        this.context.fillStyle = "gray";
        this.context.fillRect(0, 0, w, h)

        const dpr = window.devicePixelRatio || 1;
        const z = this.zoom * dpr;

        const center = {
            x: w / 2,
            y: h / 2,
        };

        this.context.setTransform(
            z,
            0,
            0,
            z,
            center.x - this.camera.x * z,
            center.y - this.camera.y * z,
        )

        this.draw_board();
        this.draw_accounts();
        this.draw_grass();
    }

    private draw_board() {
        for (let i = -this.renderDistance; i < this.renderDistance; ++i) {
            for (let j = -this.renderDistance; j < this.renderDistance; ++j) {
                const x = Math.floor(this.camera.x) + i;
                const y = Math.floor(this.camera.y) + j;

                if (x < 0) continue;
                if (y < 0) continue;

                if (x >= this.dimensions.w) continue;
                if (y >= this.dimensions.h) continue;

                if ((x + y) % 2 === 0) {
                    this.context.fillStyle = 'green';
                } else {
                    continue
                }

                this.context.fillRect(x, y, 1, 1)
            }
        }
    }

    private draw_accounts() {
        for (const [_, value] of Object.entries(this.accounts)) {
            this.context.drawImage(this.pawn, value.x, value.y, 1, 1);
        }
    }

    private draw_grass() {
        const dy = 0.25;

        for (const grass of this.grasses) {
            this.context.drawImage(this.grass, grass.x, grass.y + dy, 1, 1)
        }
    }

    private resize = () => {

        const dpr = window.devicePixelRatio || 1;
        const rect = this.canvas.getBoundingClientRect();

        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
    }

    private send_position = () => {
        this.direction.x = (this.direction_keys.left ? -1 : 0) + (this.direction_keys.right ? + 1 : 0)
        this.direction.y = (this.direction_keys.up ? -1 : 0) + (this.direction_keys.down ? + 1 : 0)

        const target = {x: this.account.x + this.direction.x, y: this.account.y + this.direction.y }

        if (target.x < 0 || target.y < 0 || target.x >= this.dimensions.w || target.y >= this.dimensions.h) return;
        if (this.direction.x === 0 && this.direction.y === 0) return;

        this.account.x = target.x
        this.account.y = target.y

        fetch('/api/position', {
            method: 'POST',
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(target),
        })
    }
}