import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combines class names with Tailwind CSS class resolution.
 * @param  {...any} inputs - Class names or conditional class objects
 * @returns {string} - Merged class string
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

/**
 * Format timestamp to a human-readable string.
 * @param {string|number|Date} date
 * @returns {string}
 */
export function formatDate(date) {
  if (!date) return "—";
  try {
    const d = new Date(date);
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(d);
  } catch {
    return String(date);
  }
}

/**
 * Truncate a string with an ellipsis.
 * @param {string} str
 * @param {number} length
 * @returns {string}
 */
export function truncate(str, length = 60) {
  if (!str) return "";
  return str.length > length ? `${str.slice(0, length)}...` : str;
}
