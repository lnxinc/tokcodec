#!/usr/bin/env node
// npx launcher for tokcodec. The engine is a Python package; this finds the
// fastest way to run it without the user installing anything by hand:
//   1. `tokcodec` already on PATH                (installed via uv/pipx)
//   2. `uvx tokcodec@<version>`                  (zero-install, cached after first run)
//   3. `pipx run tokcodec==<version>`
//   4. `python3 -m tokcodec` after a one-time `pip install --user`
'use strict';
const { spawnSync } = require('child_process');
const { version } = require('../package.json');

const args = process.argv.slice(2);
const win = process.platform === 'win32';

function has(cmd) {
  const r = spawnSync(win ? 'where' : 'sh', win ? [cmd] : ['-c', `command -v ${cmd}`], { stdio: 'ignore' });
  return r.status === 0;
}
function run(cmd, cmdArgs) {
  const r = spawnSync(cmd, cmdArgs, { stdio: 'inherit', shell: win });
  if (r.error) return null;
  return r.status === null ? 1 : r.status;
}

let status = null;
if (has('tokcodec')) {
  status = run('tokcodec', args);
} else if (has('uvx')) {
  status = run('uvx', [`tokcodec@${version}`, ...args]);
} else if (has('pipx')) {
  status = run('pipx', ['run', `tokcodec==${version}`, ...args]);
} else {
  const py = ['python3', 'python'].find(has);
  if (!py) {
    console.error('tokcodec needs Python 3.12+ (or uv / pipx). Install one of:\n' +
      '  https://docs.astral.sh/uv/   (recommended: curl -LsSf https://astral.sh/uv/install.sh | sh)\n' +
      '  https://www.python.org/downloads/');
    process.exit(1);
  }
  const probe = spawnSync(py, ['-m', 'tokcodec', '--version'], { stdio: 'ignore' });
  if (probe.status !== 0) {
    console.error(`installing tokcodec ${version} into your user site-packages (one time)...`);
    const pip = run(py, ['-m', 'pip', 'install', '--user', '--quiet', `tokcodec==${version}`]);
    if (pip !== 0) { console.error('pip install failed'); process.exit(pip || 1); }
  }
  status = run(py, ['-m', 'tokcodec', ...args]);
}
process.exit(status === null ? 1 : status);
