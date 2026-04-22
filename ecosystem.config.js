module.exports = {
  apps: [{
    name: 'investai',
    script: '/data/inscesteAI/venv/bin/uvicorn',
    args: 'api.main:app --host 0.0.0.0 --port 8091',
    cwd: '/data/inscesteAI',
    interpreter: 'none',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      PYTHONPATH: '/data/inscesteAI',
      PATH: '/data/inscesteAI/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
    },
    error_file: '/data/inscesteAI/logs/error.log',
    out_file: '/data/inscesteAI/logs/out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
  }]
}
