(function (root) {
  'use strict';

  const key = 'mill-demo-session';
  const roles = ['owner', 'editor', 'viewer'];
  const providers = ['Google', 'Microsoft'];
  const read = () => {
    try {
      const session = JSON.parse(sessionStorage.getItem(key));
      return session && roles.includes(session.role) && providers.includes(session.provider) ? session : null;
    } catch { return null; }
  };
  let session = read();

  root.MillDemoAuth = {
    get session() { return session; },
    signIn(provider, role) {
      if (!providers.includes(provider) || !roles.includes(role)) return false;
      session = { provider, role, name: role === 'owner' ? 'Илья' : role === 'editor' ? 'Редактор' : 'Наблюдатель' };
      try { sessionStorage.setItem(key, JSON.stringify(session)); } catch {}
      return true;
    },
    signOut() {
      session = null;
      try { sessionStorage.removeItem(key); } catch {}
    },
    canView(page) {
      if (!session) return false;
      if (['channels', 'leads', 'checks'].includes(page)) return session.role === 'owner';
      if (page === 'create') return session.role !== 'viewer';
      return true;
    },
    canEdit(page) {
      if (!session || session.role === 'viewer') return false;
      if (['channels', 'leads', 'checks'].includes(page)) return session.role === 'owner';
      return true;
    }
  };
})(window);
