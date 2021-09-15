import { writable } from 'svelte/store'

export const boards = writable([]);
export const currentBoard = writable(null);
export const loading = writable(false);
export const threads = writable([]);