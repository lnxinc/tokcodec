#!/usr/bin/env node
// npx launcher for tokcodec. The engine is a Python package; this finds the
// fastest way to run it, and needs nothing but Node to be installed:
//   1. `tokcodec` already on PATH                     (installed via uv/pipx)
//   2. `uvx tokcodec@<version>`                       (uv already installed)
//   3. `pipx run tokcodec==<version>`
//   4. a private copy of `uv` in the tokcodec cache   (downloaded once, ~15 MB)
//      uv then fetches its own Python 3.12 if the machine has none.
// Set TOKCODEC_NO_BOOTSTRAP=1 to disable step 4 and get an error instead.
// Set TOKCODEC_PYTHON_SPEC to override what uv/pipx run (e.g. a local checkout path) for testing.
'use strict';
const { spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { version } = require('../package.json');

const args = process.argv.slice(2);
const spec = process.env.TOKCODEC_PYTHON_SPEC || `tokcodec@${version}`;
const win = process.platform === 'win32';
const exe = win ? '.exe' : '';

function has(cmd) {
  const r = spawnSync(win ? 'where' : 'sh', win ? [cmd] : ['-c', `command -v ${cmd}`], { encoding: 'utf8' });
  return r.status === 0;
}
// A real `tokcodec` on PATH, ignoring npm/npx shims of this very launcher
// (npx puts the package's own bin on PATH, which would recurse forever).
function realTokcodec() {
  const r = spawnSync(win ? 'where' : 'sh', win ? ['tokcodec'] : ['-c', 'command -v tokcodec'], { encoding: 'utf8' });
  if (r.status !== 0) return null;
  const self = fs.realpathSync(__filename);
  for (const line of r.stdout.split(/\r?\n/).map((l) => l.trim()).filter(Boolean)) {
    if (/node_modules|_npx/.test(line)) continue;
    try { if (fs.realpathSync(line) === self) continue; } catch (_) {}
    try {
      const head = fs.readFileSync(line, 'utf8').slice(0, 400);
      if (/tokcodec\.js/.test(head)) continue;  // .cmd / shell shim pointing at this launcher
    } catch (_) {}
    return line;
  }
  return null;
}
function run(cmd, cmdArgs) {
  const r = spawnSync(cmd, cmdArgs, { stdio: 'inherit', shell: win });
  if (r.error) return null;
  return r.status === null ? 1 : r.status;
}

function cacheDir() {
  if (process.env.TOKCODEC_CACHE_DIR) return process.env.TOKCODEC_CACHE_DIR;
  if (win) return path.join(process.env.LOCALAPPDATA || os.homedir(), 'tokcodec', 'uv');
  return path.join(process.env.XDG_CACHE_HOME || path.join(os.homedir(), '.cache'), 'tokcodec', 'uv');
}

function uvTarget() {
  const arch = { x64: 'x86_64', arm64: 'aarch64' }[process.arch];
  if (!arch) return null;
  if (process.platform === 'darwin') return `uv-${arch}-apple-darwin.tar.gz`;
  if (win) return `uv-${arch}-pc-windows-msvc.zip`;
  if (process.platform === 'linux') {
    let libc = 'gnu';
    try { if (!process.report.getReport().header.glibcVersionRuntime) libc = 'musl'; } catch (_) {}
    return `uv-${arch}-unknown-linux-${libc}.tar.gz`;
  }
  return null;
}

async function bootstrapUv() {
  const dir = cacheDir();
  const uv = path.join(dir, 'uv' + exe);
  if (fs.existsSync(uv)) return uv;
  const asset = uvTarget();
  if (!asset) throw new Error(`no uv build for ${process.platform}/${process.arch}`);
  const url = `https://github.com/astral-sh/uv/releases/latest/download/${asset}`;
  console.error(`tokcodec: no Python toolchain found; downloading uv once into ${dir} ...`);
  fs.mkdirSync(dir, { recursive: true });
  const res = await fetch(url, { redirect: 'follow' });
  if (!res.ok) throw new Error(`download failed: ${res.status} ${url}`);
  const archive = path.join(dir, asset);
  fs.writeFileSync(archive, Buffer.from(await res.arrayBuffer()));
  // tar handles .tar.gz everywhere and .zip on Windows 10+ (bsdtar)
  const tarArgs = asset.endsWith('.zip') ? ['-xf', archive, '-C', dir] : ['-xzf', archive, '--strip-components=1', '-C', dir];
  const t = spawnSync('tar', tarArgs, { stdio: 'inherit' });
  fs.rmSync(archive, { force: true });
  if (t.status !== 0 || !fs.existsSync(uv)) throw new Error('could not extract uv');
  if (!win) fs.chmodSync(uv, 0o755);
  return uv;
}

async function main() {
  const real = realTokcodec();
  if (real) return run(real, args);
  if (has('uvx')) return run('uvx', ['--from', spec, 'tokcodec', ...args]);
  if (has('pipx')) return run('pipx', ['run', '--spec', spec, 'tokcodec', ...args]);
  if (process.env.TOKCODEC_NO_BOOTSTRAP) {
    console.error('tokcodec needs Python 3.12+ via uv or pipx. Install uv: https://docs.astral.sh/uv/');
    return 1;
  }
  let uv;
  try {
    uv = await bootstrapUv();
  } catch (e) {
    console.error(`tokcodec: ${e.message}\nInstall uv manually (https://docs.astral.sh/uv/) and re-run.`);
    return 1;
  }
  return run(uv, ['tool', 'run', '--quiet', '--from', spec, 'tokcodec', ...args]);
}

main().then((s) => process.exit(s === null ? 1 : s), (e) => { console.error(e); process.exit(1); });
