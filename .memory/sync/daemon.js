#!/usr/bin/env node

/**
 * Memory Synchronization Daemon
 * 
 * Runs continuously to:
 * 1. Auto-save Claude sessions every N minutes
 * 2. Watch for file changes and sync context
 * 3. Poll GitHub for Cursor/external updates
 * 4. Commit memory updates to GitHub
 * 5. Detect and resolve conflicts
 */

const fs = require('fs').promises;
const path = require('path');
const chokidar = require('chokidar');
const { execSync } = require('child_process');

const CONFIG_PATH = path.join(__dirname, '../config.json');
const STATE_PATH = path.join(__dirname, '../.sync-state.json');

class MemorySyncDaemon {
  constructor() {
    this.config = null;
    this.state = null;
    this.watchers = [];
    this.intervals = [];
  }

  async init() {
    console.log('🧠 Initializing Memory Sync Daemon...');
    
    // Load configuration
    this.config = JSON.parse(await fs.readFile(CONFIG_PATH, 'utf-8'));
    
    // Load or create state
    try {
      this.state = JSON.parse(await fs.readFile(STATE_PATH, 'utf-8'));
    } catch {
      this.state = {
        lastSessionSave: null,
        lastGitHubPull: null,
        lastGitHubPush: null,
        sessionCount: 0,
        syncCount: 0,
        checksums: {}
      };
    }

    console.log('✅ Configuration loaded');
  }

  async start() {
    await this.init();

    // Start all automatic processes
    if (this.config.autoSave.enabled) {
      this.startSessionAutoSave();
    }

    if (this.config.contextSync.enabled) {
      this.startContextWatcher();
    }

    if (this.config.github.autoPull) {
      this.startGitHubPuller();
    }

    if (this.config.crossTool.claudeCheckGitHubInterval) {
      this.startCrossToolSync();
    }

    console.log('🚀 Memory Sync Daemon started');
    console.log(`   Session auto-save: every ${this.config.autoSave.intervalMinutes}m`);
    console.log(`   GitHub pull: every ${this.config.github.pullIntervalMinutes}m`);
    console.log(`   Cross-tool sync: every ${this.config.crossTool.claudeCheckGitHubInterval}s`);
  }

  // ==================== SESSION AUTO-SAVE ====================

  startSessionAutoSave() {
    const intervalMs = this.config.autoSave.intervalMinutes * 60 * 1000;
    
    const interval = setInterval(async () => {
      await this.saveSession();
    }, intervalMs);

    this.intervals.push(interval);
    console.log('📝 Session auto-save enabled');
  }

  async saveSession() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const sessionPath = path.join(__dirname, '../sessions', `session-${timestamp}.json`);

    const session = {
      timestamp: new Date().toISOString(),
      conversationId: process.env.CLAUDE_CONVERSATION_ID || 'unknown',
      snapshot: {
        type: 'auto-save',
        trigger: 'interval',
        projectState: await this.captureProjectState(),
        recentDecisions: await this.extractRecentDecisions(),
        activeFiles: await this.getActiveFiles(),
        keyTopics: await this.extractKeyTopics()
      }
    };

    await fs.mkdir(path.dirname(sessionPath), { recursive: true });
    await fs.writeFile(sessionPath, JSON.stringify(session, null, 2));

    this.state.lastSessionSave = new Date().toISOString();
    this.state.sessionCount++;
    await this.saveState();

    console.log(`💾 Session saved: ${path.basename(sessionPath)}`);

    // Auto-commit to GitHub
    if (this.config.github.autoCommit) {
      await this.commitToGitHub([sessionPath], `Auto-save session ${this.state.sessionCount}`);
    }

    // Update active context
    await this.updateActiveContext(session);
  }

  async captureProjectState() {
    return {
      dockerStatus: this.getDockerStatus(),
      gitBranch: this.getGitBranch(),
      gitCommit: this.getGitCommit(),
      modifiedFiles: this.getGitModified(),
      packageVersion: await this.getPackageVersion()
    };
  }

  async extractRecentDecisions() {
    // Parse recent conversation for decisions
    // This would integrate with Claude's conversation history
    return [];
  }

  async getActiveFiles() {
    try {
      const recent = execSync('git diff --name-only HEAD~5..HEAD', { encoding: 'utf-8' });
      return recent.split('\n').filter(Boolean);
    } catch {
      return [];
    }
  }

  async extractKeyTopics() {
    // Extract key topics from recent conversation
    // This would analyze conversation content
    return ['docker', 'memory-sync', 'automation'];
  }

  // ==================== CONTEXT WATCHER ====================

  startContextWatcher() {
    const watcher = chokidar.watch(this.config.contextSync.watchPaths, {
      ignored: /(^|[\/\\])\../, // ignore dotfiles except our own
      persistent: true,
      ignoreInitial: true
    });

    watcher
      .on('change', async (filepath) => {
        console.log(`📝 File changed: ${filepath}`);
        await this.syncContext(filepath, 'change');
      })
      .on('add', async (filepath) => {
        console.log(`➕ File added: ${filepath}`);
        await this.syncContext(filepath, 'add');
      });

    this.watchers.push(watcher);
    console.log('👀 Context watcher enabled');
  }

  async syncContext(filepath, event) {
    // Update checksums
    const content = await fs.readFile(filepath, 'utf-8');
    const checksum = this.calculateChecksum(content);
    
    if (this.state.checksums[filepath] === checksum) {
      return; // No actual change
    }

    this.state.checksums[filepath] = checksum;

    // Generate context update
    const contextUpdate = {
      timestamp: new Date().toISOString(),
      file: filepath,
      event: event,
      checksum: checksum,
      summary: await this.summarizeChange(filepath, content)
    };

    // Write to active context
    await this.appendToActiveContext(contextUpdate);

    // Sync to all targets
    for (const target of this.config.contextSync.syncTargets) {
      await this.syncToTarget(contextUpdate, target);
    }

    this.state.syncCount++;
    await this.saveState();

    // Auto-commit
    if (this.config.github.autoCommit && this.shouldCommit(filepath)) {
      await this.commitToGitHub(
        [filepath, '.memory/context/active-context.md'],
        `Update context: ${path.basename(filepath)}`
      );
    }
  }

  async summarizeChange(filepath, content) {
    const lines = content.split('\n').length;
    const ext = path.extname(filepath);
    return `${ext} file with ${lines} lines`;
  }

  // ==================== GITHUB SYNC ====================

  startGitHubPuller() {
    const intervalMs = this.config.github.pullIntervalMinutes * 60 * 1000;
    
    const interval = setInterval(async () => {
      await this.pullFromGitHub();
    }, intervalMs);

    this.intervals.push(interval);
    console.log('⬇️  GitHub auto-pull enabled');
  }

  async pullFromGitHub() {
    try {
      console.log('⬇️  Pulling from GitHub...');
      
      // Fetch latest
      execSync('git fetch origin', { stdio: 'ignore' });
      
      // Check for remote changes in memory paths
      const diff = execSync('git diff --name-only HEAD origin/main', { encoding: 'utf-8' });
      const memoryChanges = diff.split('\n').filter(f => 
        f.startsWith('.memory/') || 
        f.startsWith('.cursor/context/') ||
        f.startsWith('docs/context/')
      );

      if (memoryChanges.length > 0) {
        console.log(`   Found ${memoryChanges.length} remote changes`);
        
        // Pull changes
        execSync('git pull origin main --no-rebase', { stdio: 'inherit' });
        
        // Reload context
        await this.reloadContext();
        
        this.state.lastGitHubPull = new Date().toISOString();
        await this.saveState();
        
        console.log('✅ Context updated from GitHub');
      }
    } catch (error) {
      console.error('❌ GitHub pull failed:', error.message);
    }
  }

  async commitToGitHub(files, message) {
    try {
      for (const file of files) {
        execSync(`git add "${file}"`, { stdio: 'ignore' });
      }
      
      const commitMsg = `${this.config.github.commitMessagePrefix} ${message}`;
      execSync(`git commit -m "${commitMsg}"`, { stdio: 'ignore' });
      execSync('git push origin main', { stdio: 'ignore' });
      
      this.state.lastGitHubPush = new Date().toISOString();
      await this.saveState();
      
      console.log(`⬆️  Committed to GitHub: ${message}`);
    } catch (error) {
      // Ignore if no changes
      if (!error.message.includes('nothing to commit')) {
        console.error('❌ GitHub commit failed:', error.message);
      }
    }
  }

  shouldCommit(filepath) {
    return this.config.github.autoCommitPaths.some(pattern => {
      const regex = new RegExp(pattern.replace('**', '.*').replace('*', '[^/]*'));
      return regex.test(filepath);
    });
  }

  // ==================== CROSS-TOOL SYNC ====================

  startCrossToolSync() {
    const intervalMs = this.config.crossTool.claudeCheckGitHubInterval * 1000;
    
    const interval = setInterval(async () => {
      await this.checkForExternalUpdates();
    }, intervalMs);

    this.intervals.push(interval);
    console.log('🔄 Cross-tool sync enabled');
  }

  async checkForExternalUpdates() {
    // Check if Cursor has made updates
    if (this.config.crossTool.cursorReadsclaude) {
      await this.pullFromGitHub();
    }

    // Update cursors context with latest Claude state
    if (this.config.crossTool.claudeReadsCursor) {
      await this.syncToCursor();
    }
  }

  async syncToCursor() {
    const cursorContextPath = path.join(__dirname, '../../.cursor/context');
    const activeContextPath = path.join(__dirname, '../context/active-context.md');

    try {
      const content = await fs.readFile(activeContextPath, 'utf-8');
      await fs.mkdir(cursorContextPath, { recursive: true });
      await fs.writeFile(
        path.join(cursorContextPath, 'from-claude.md'),
        content
      );
    } catch (error) {
      // Context file might not exist yet
    }
  }

  // ==================== CONTEXT MANAGEMENT ====================

  async updateActiveContext(session) {
    const contextPath = path.join(__dirname, '../context/active-context.md');
    
    const content = `# Active Context - ${new Date().toISOString()}

## Current Session
- ID: ${session.conversationId}
- Timestamp: ${session.timestamp}
- Session Count: ${this.state.sessionCount}

## Project State
\`\`\`json
${JSON.stringify(session.snapshot.projectState, null, 2)}
\`\`\`

## Recent Decisions
${session.snapshot.recentDecisions.map(d => `- ${d}`).join('\n') || 'None'}

## Active Files
${session.snapshot.activeFiles.map(f => `- ${f}`).join('\n') || 'None'}

## Key Topics
${session.snapshot.keyTopics.map(t => `- ${t}`).join('\n')}

---
Last updated: ${new Date().toISOString()}
Auto-generated by Memory Sync Daemon
`;

    await fs.mkdir(path.dirname(contextPath), { recursive: true });
    await fs.writeFile(contextPath, content);
  }

  async appendToActiveContext(update) {
    const contextPath = path.join(__dirname, '../context/active-context.md');
    
    try {
      let content = await fs.readFile(contextPath, 'utf-8');
      content += `\n\n## Update: ${update.timestamp}\n`;
      content += `- File: ${update.file}\n`;
      content += `- Event: ${update.event}\n`;
      content += `- Summary: ${update.summary}\n`;
      
      await fs.writeFile(contextPath, content);
    } catch {
      // File doesn't exist yet
    }
  }

  async syncToTarget(update, targetDir) {
    const targetPath = path.join(__dirname, '../../', targetDir, 'latest-update.json');
    await fs.mkdir(path.dirname(targetPath), { recursive: true });
    await fs.writeFile(targetPath, JSON.stringify(update, null, 2));
  }

  async reloadContext() {
    console.log('🔄 Reloading context from disk...');
    // This would trigger a context reload in Claude
    // For now, just log the action
  }

  // ==================== UTILITIES ====================

  calculateChecksum(content) {
    const crypto = require('crypto');
    return crypto.createHash('md5').update(content).digest('hex');
  }

  getDockerStatus() {
    try {
      const output = execSync('docker ps --format "{{.Names}}" 2>/dev/null', { encoding: 'utf-8' });
      return output.split('\n').filter(Boolean);
    } catch {
      return [];
    }
  }

  getGitBranch() {
    try {
      return execSync('git branch --show-current', { encoding: 'utf-8' }).trim();
    } catch {
      return 'unknown';
    }
  }

  getGitCommit() {
    try {
      return execSync('git rev-parse --short HEAD', { encoding: 'utf-8' }).trim();
    } catch {
      return 'unknown';
    }
  }

  getGitModified() {
    try {
      const output = execSync('git status --porcelain', { encoding: 'utf-8' });
      return output.split('\n').filter(Boolean).map(line => line.slice(3));
    } catch {
      return [];
    }
  }

  async getPackageVersion() {
    try {
      const pkg = JSON.parse(await fs.readFile('package.json', 'utf-8'));
      return pkg.version;
    } catch {
      return 'unknown';
    }
  }

  async saveState() {
    await fs.writeFile(STATE_PATH, JSON.stringify(this.state, null, 2));
  }

  async stop() {
    console.log('🛑 Stopping Memory Sync Daemon...');
    
    // Stop all watchers
    for (const watcher of this.watchers) {
      await watcher.close();
    }
    
    // Clear all intervals
    for (const interval of this.intervals) {
      clearInterval(interval);
    }
    
    await this.saveState();
    console.log('✅ Daemon stopped');
  }
}

// ==================== MAIN ====================

const daemon = new MemorySyncDaemon();

daemon.start().catch(error => {
  console.error('❌ Fatal error:', error);
  process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', async () => {
  await daemon.stop();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  await daemon.stop();
  process.exit(0);
});
