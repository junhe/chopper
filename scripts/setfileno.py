
setting = """
*           soft    nofile          4096
*           hard    nofile          63536
"""
with open('/etc/security/limits.conf', 'a') as f:
    f.write(setting)
