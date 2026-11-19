/* Shared window chrome for the Direction B mockups: title row + sidebar.
 * <header class="titlebar"></header> and <aside class="sidebar" data-current="kontrol|degerler"></aside>
 * are filled here so both pages show identical chrome. Invented data only. */
(function () {
  const ic = (n, c = '') => `<svg class="i ${c}" aria-hidden="true"><use href="#${n}"/></svg>`;
  const mark = `<svg class="mark" viewBox="0 0 256 256" aria-hidden="true"><rect width="256" height="256" rx="56" fill="#3f5a4c"/>
    <g transform="translate(25.6 25.6) scale(.8)"><path d="M44 51l14-25h36l14 25z" fill="#e9d9a6"/>
    <path d="M41 50h174a9 9 0 0 1 9 9v22a9 9 0 0 1-9 9H41a9 9 0 0 1-9-9V59a9 9 0 0 1 9-9z" fill="#e9d9a6"/>
    <path d="M96 121l14-25h36l14 25z" fill="#e8731a"/>
    <path d="M41 120h174a9 9 0 0 1 9 9v22a9 9 0 0 1-9 9H41a9 9 0 0 1-9-9v-22a9 9 0 0 1 9-9z" fill="#e9d9a6"/>
    <path d="M148 191l14-25h36l14 25z" fill="#e9d9a6"/>
    <path d="M41 190h174a9 9 0 0 1 9 9v22a9 9 0 0 1-9 9H41a9 9 0 0 1-9-9v-22a9 9 0 0 1 9-9z" fill="#e9d9a6"/></g></svg>`;

  for (const tb of document.querySelectorAll('header.titlebar')) {
    tb.innerHTML = `
      <div class="tb-app">
        <button class="ibtn" aria-label="Uygulama menüsü (Alt)" aria-haspopup="menu">${ic('menu')}</button>
        ${mark}<span class="name">Evrakçı</span>
      </div>
      <div class="tb-center"><div class="cmd" role="button" aria-label="Komut paleti (Ctrl+K)">${ic('search', 'sm')}
        <span>Komut, belge veya sayfa ara</span><span class="hint">Ctrl+K</span></div></div>
      <div class="tb-right">
        <span class="save">${ic('check', 'sm')}Kaydedildi 14:32</span>
        <div class="caption" aria-hidden="true">
          <span><svg viewBox="0 0 10 10"><path d="M0 5.5h10"/></svg></span>
          <span><svg viewBox="0 0 10 10"><rect x=".5" y=".5" width="9" height="9" rx="1"/></svg></span>
          <span><svg viewBox="0 0 10 10"><path d="M.5.5l9 9M9.5.5l-9 9"/></svg></span>
        </div>
      </div>`;
  }

  for (const sb of document.querySelectorAll('aside.sidebar')) {
    const cur = sb.dataset.current;
    const row = (id, icon, label, count = '', key) => `
      <div class="nav-row" ${cur === id ? 'aria-current="page"' : ''} aria-label="${label} (Ctrl+${key})">
        ${ic(icon)}<span>${label}</span>${count}</div>`;
    const check = n => `<span class="count check">${ic('triangle-alert', 'xs')}${n}</span>`;
    const plain = n => `<span class="count">${n}</span>`;
    sb.innerHTML = `
      <div class="job" role="button" aria-label="İş değiştir">
        <span class="name">Kasım 2026 kapasite raporları</span>${ic('chevron-down', 'sm')}
        <span class="meta">640 sayfa, 96 belge</span>
      </div>
      <nav class="nav" aria-label="Bölümler">
        ${row('yukle', 'file-up', 'Yükle', plain(4), 1)}
        ${row('kontrol', 'files', 'Kontrol', check(7), 2)}
        ${row('sablonlar', 'scan-text', 'Şablonlar', plain(2), 3)}
        ${row('degerler', 'table-2', 'Değerler', check(14), 4)}
        ${cur === 'degerler' ? `
          <div class="nav-row sub" aria-label="Kontrol gerekenler, 14 değer"><span>Kontrol gerekenler</span><span class="count check">14</span></div>
          <div class="nav-row sub" aria-current="true"><span>İncelenmemiş</span><span class="count">105</span></div>
          <div class="nav-row sub"><span>Tümü</span><span class="count">152</span></div>` : ''}
        ${row('disa', 'folder-output', 'Dışa Aktar', '', 5)}
        ${row('rehber', 'book-open', 'Rehber', '', 6)}
      </nav>
      <div class="sb-label">Son işler</div>
      <div class="sb-item">Ekim sicil kayıtları</div>
      <div class="sb-item">Eylül kapasite raporları</div>
      <div class="sb-foot">
        <div class="progress-line">
          <div class="row"><span>İncelendi</span><span><b>58</b> / 96 belge</span></div>
          <div class="bar"><i style="width:60.4%"></i></div>
        </div>
        <div class="sb-tools">
          <button class="ibtn quiet" aria-label="Ayarlar (Ctrl+,)">${ic('settings')}</button>
          <button class="ibtn quiet" aria-label="Yardım (F1)">${ic('circle-help')}</button>
          <span class="grow"></span>
          <button class="ibtn quiet" aria-label="Kenar çubuğunu daralt (Ctrl+B)">${ic('panel-left')}</button>
        </div>
      </div>`;
  }
})();
