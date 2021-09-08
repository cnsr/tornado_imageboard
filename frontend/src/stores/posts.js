import { writable } from 'svelte/store'

export const posts = writable([]);
export const currentPost = writable(null); // is this even needed?