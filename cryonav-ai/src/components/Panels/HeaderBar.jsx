const HeaderBar = ({ connectionStatus, missionTime }) => {
  const isLive = connectionStatus === 'connected';
  const isChecking = connectionStatus === 'checking';
  const label = isLive ? 'ACTIVE' : isChecking ? 'CHECKING' : 'SIM MODE';

  return (
    <header className="header-bar">
      <div className="header-left">
        <div className="header-logo" aria-hidden="true">
          ❄
        </div>
        <div className="header-title-wrap">
          <div className="header-title">CryoNav AI</div>
          <div className="header-subtitle">Chennai Port → Maitri Station · Indian Antarctic Expedition</div>
        </div>
      </div>

      <div className="header-right">
        {missionTime && (
          <span className="header-subtitle" style={{ color: '#94a3b8', fontFamily: 'monospace' }}>
            {missionTime}
          </span>
        )}
        <div className="connection-pill">
          <span className={`status-dot ${isLive ? 'active' : 'offline'}`} />
          {label}
        </div>
      </div>
    </header>
  );
};

export default HeaderBar;
