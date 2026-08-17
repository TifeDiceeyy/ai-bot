const isWindows = process.platform === "win32";

module.exports = {
  apps: [
    {
      name: "ai-bot",
      cwd: __dirname,
      script: isWindows
        ? "python/.venv/Scripts/studio-ai-bot.exe"
        : "python/.venv/bin/studio-ai-bot",
      interpreter: "none",
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      stop_exit_codes: [78],
      exp_backoff_restart_delay: 1000,
      max_restarts: 10,
      min_uptime: "10s",
      time: true,
    },
  ],
};
