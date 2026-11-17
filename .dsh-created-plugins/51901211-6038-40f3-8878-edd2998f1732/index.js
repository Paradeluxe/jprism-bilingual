/**
 * Host half of the jspace dashboard bundle.
 *
 * The whole interface is Client-side (client.js): a resident right-Sidebar tab
 * that embeds the dashboard page served at http://127.0.0.1:8904/. The Host row
 * only makes this package an active Loader source so its `dsh.client` half is
 * composed into the Web UI; it reads no files, starts nothing, and serves none
 * of the dashboard data itself.
 */
export function apply() {}
