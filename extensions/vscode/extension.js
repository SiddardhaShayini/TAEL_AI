const vscode = require('vscode');
const http = require('http');

/**
 * Helper to make HTTP JSON requests to local TAEL API service
 */
function requestTael(method, path, body = null, config) {
  return new Promise((resolve, reject) => {
    const serviceUrl = new URL(config.get('serviceUrl', 'http://127.0.0.1:7860'));
    const authToken = config.get('authToken', '');

    const options = {
      hostname: serviceUrl.hostname,
      port: serviceUrl.port || 7860,
      path: path,
      method: method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (authToken) {
      options.headers['Authorization'] = `Bearer ${authToken}`;
    }

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(parsed);
          } else {
            reject(new Error(parsed.detail || `Request failed with status ${res.statusCode}`));
          }
        } catch (e) {
          resolve(data);
        }
      });
    });

    req.on('error', (err) => {
      reject(err);
    });

    if (body) {
      req.write(JSON.stringify(body));
    }
    req.end();
  });
}

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
  const getCfg = () => vscode.workspace.getConfiguration('tael');

  // 1. Open Web Studio in VS Code Editor Column
  const openStudioCmd = vscode.commands.registerCommand('tael.openStudio', () => {
    const serviceUrl = getCfg().get('serviceUrl', 'http://127.0.0.1:7860');
    const panel = vscode.window.createWebviewPanel(
      'taelStudio',
      'TAEL AI Studio',
      vscode.ViewColumn.Beside,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
      }
    );

    panel.webview.html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>
    body, html { margin: 0; padding: 0; height: 100%; overflow: hidden; }
    iframe { width: 100%; height: 100%; border: none; }
  </style>
</head>
<body>
  <iframe src="${serviceUrl}"></iframe>
</body>
</html>`;
  });

  // 2. Quick Chat Prompt
  const chatCmd = vscode.commands.registerCommand('tael.chat', async () => {
    const prompt = await vscode.window.showInputBox({
      prompt: 'Enter task, question, or code instruction for TAEL',
      placeHolder: 'e.g. Inspect the current workspace and explain the test setup...',
    });

    if (!prompt) return;

    vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'TAEL AI executing task...',
        cancellable: false,
      },
      async () => {
        try {
          const workspaceFolders = vscode.workspace.workspaceFolders;
          const rootPath = workspaceFolders ? workspaceFolders[0].uri.fsPath : undefined;

          // Create session
          const session = await requestTael('POST', '/session', { workspace_root: rootPath }, getCfg());
          // Execute task
          const result = await requestTael('POST', `/session/${session.session_id}/chat`, { prompt, max_turns: 8 }, getCfg());

          const action = await vscode.window.showInformationMessage(
            `TAEL: ${result.final_answer.slice(0, 120)}...`,
            'Open Studio',
            'Dismiss'
          );
          if (action === 'Open Studio') {
            vscode.commands.executeCommand('tael.openStudio');
          }
        } catch (err) {
          vscode.window.showErrorMessage(`TAEL AI Error: ${err.message}. Is the TAEL service running?`);
        }
      }
    );
  });

  // 3. Run Doctor Diagnostics in Terminal
  const doctorCmd = vscode.commands.registerCommand('tael.doctor', () => {
    const terminal = vscode.window.createTerminal('TAEL Doctor');
    terminal.show();
    terminal.sendText('tael doctor');
  });

  // 4. Create Workspace Checkpoint
  const checkpointCmd = vscode.commands.registerCommand('tael.checkpoint', async () => {
    const description = await vscode.window.showInputBox({
      prompt: 'Describe this workspace checkpoint',
      placeHolder: 'e.g. Before refactoring orchestrator',
    });

    if (!description) return;

    try {
      const res = await requestTael('POST', '/checkpoints', { description }, getCfg());
      vscode.window.showInformationMessage(`TAEL Checkpoint created: ${res.id} (${res.description})`);
    } catch (err) {
      vscode.window.showErrorMessage(`Failed to create checkpoint: ${err.message}`);
    }
  });

  // 5. Rollback Workspace
  const rollbackCmd = vscode.commands.registerCommand('tael.rollback', async () => {
    try {
      const checkpoints = await requestTael('GET', '/checkpoints', null, getCfg());
      if (!Array.isArray(checkpoints) || checkpoints.length === 0) {
        vscode.window.showInformationMessage('No TAEL checkpoints found.');
        return;
      }

      const items = checkpoints.map((c) => ({
        label: `${c.id}: ${c.description}`,
        description: c.timestamp,
        checkpointId: c.id,
      }));

      const selected = await vscode.window.showQuickPick(items, {
        placeHolder: 'Select a checkpoint to restore workspace',
      });

      if (!selected) return;

      const confirm = await vscode.window.showWarningMessage(
        `Roll back workspace to "${selected.label}"? Any uncommitted changes will be replaced.`,
        { modal: true },
        'Proceed with Rollback'
      );

      if (confirm === 'Proceed with Rollback') {
        await requestTael('POST', '/rollback', { checkpoint_id: selected.checkpointId }, getCfg());
        vscode.window.showInformationMessage(`Successfully rolled back to checkpoint: ${selected.checkpointId}`);
      }
    } catch (err) {
      vscode.window.showErrorMessage(`Rollback failed: ${err.message}`);
    }
  });

  context.subscriptions.push(openStudioCmd, chatCmd, doctorCmd, checkpointCmd, rollbackCmd);
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
