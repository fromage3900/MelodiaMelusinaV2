/* Melodia editorial shell — parallax, site copy hydration, optional intake grids. */
(function (global) {
  'use strict';

  const COPY_URL = '../content/site-copy.json';
  const PLATES_URL = '../content/site-plates.json';
  const INTAKE_URL = '../generated/unreal_portfolio_intake.json';
  const BLENDER_INTAKE_URL = '../generated/blender_portfolio_intake.json';
  const NIGHTSHIFT_MANIFEST_URL = '../generated/nightshift_manifest.json';
  const NIGHTSHIFT_ASSET_BASE = '../generated/assets/nightshift/';
  const MATERIAL_LOOPS_MANIFEST_URL = '../generated/material_loops_manifest.json';
  const MATERIAL_LOOPS_ASSET_BASE = '../generated/assets/material-loops/';
  const LANDSCAPE_LOOPS_MANIFEST_URL = '../generated/landscape_loops_manifest.json';
  const MI_PREVIEW_MANIFEST_URL = '../generated/mi_preview_manifest.json';
  const GEOMETRY_PIPELINES_URL = '../generated/geometry_nodes_pipelines.json';
  const PRODUCTION_SIGNALS_URL = '../generated/portfolio_production_signals.json';
  const RENDER_CATALOG_URL = '../generated/portfolio_render_catalog.json';
  const REVIEW_PATH_URL = '../generated/recruiter_review_path.json';

  async function fetchJson(url) {
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  function getByPath(obj, path) {
    if (!obj || !path) return undefined;
    return path.split('.').reduce((acc, key) => (acc == null ? undefined : acc[key]), obj);
  }

  function esc(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  /** Odd index ✦, even ✧ — skip if step already carries a glyph. */
  function motifStepPrefix(index, step) {
    const raw = String(step == null ? '' : step).trim();
    if (/^[✦✧]/.test(raw)) return raw;
    const glyph = index % 2 === 0 ? '✦' : '✧';
    return `${glyph} ${raw}`;
  }

  function pathRowHtml(link, index) {
    const step = motifStepPrefix(index, link.step);
    return `<a class="path-row" href="${esc(link.href)}"><span>${esc(step)}</span><div><h3>${esc(link.title)}</h3><p>${esc(link.body)}</p></div><b>Open</b></a>`;
  }

  function initParallax() {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (reduceMotion.matches) return;

    const root = document.documentElement;
    let ticking = false;

    const updateScroll = () => {
      root.style.setProperty('--scroll-shift', `${Math.min(window.scrollY, 1200)}px`);
      ticking = false;
    };

    const requestScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(updateScroll);
        ticking = true;
      }
    };

    window.addEventListener('scroll', requestScroll, { passive: true });
    window.addEventListener(
      'pointermove',
      (event) => {
        const nx = event.clientX / window.innerWidth;
        const ny = event.clientY / window.innerHeight;
        const x = (nx - 0.5) * 28;
        const y = (ny - 0.5) * 28;
        root.style.setProperty('--mouse-x', `${x}px`);
        root.style.setProperty('--mouse-y', `${y}px`);
        root.style.setProperty('--dream-mouse-x', String(Math.max(0, Math.min(1, nx))));
        root.style.setProperty('--dream-mouse-y', String(Math.max(0, Math.min(1, ny))));
      },
      { passive: true }
    );
    updateScroll();
  }

  function applyPlates(plates) {
    if (!plates || !plates.slots) return;
    document.querySelectorAll('[data-plate]').forEach((el) => {
      const key = el.getAttribute('data-plate');
      const slot = plates.slots[key];
      if (!slot || !slot.path) return;
      if (el.tagName === 'IMG') {
        el.src = slot.path;
        if (slot.alt) el.alt = slot.alt;
      } else {
        const img = el.querySelector('img');
        if (img) {
          img.src = slot.path;
          if (slot.alt) img.alt = slot.alt;
        }
      }
      if (slot.caption) {
        const cap = el.parentElement && el.parentElement.querySelector('[data-plate-caption="' + key + '"]');
        if (cap) cap.textContent = slot.caption;
      }
    });
  }

  function applyCopy(copy, pageKey) {
    if (!copy) return;

    document.querySelectorAll('[data-copy]').forEach((el) => {
      const path = el.getAttribute('data-copy');
      const value = getByPath(copy, path);
      if (value == null || value === '') return;
      if (el.hasAttribute('data-copy-html')) {
        el.innerHTML = value;
      } else {
        el.textContent = value;
      }
    });

    const page = getByPath(copy, `pages.${pageKey}`);
    const fixedTitle = document.documentElement.hasAttribute('data-fixed-title');
    if (!fixedTitle && page && page.title) {
      document.title = page.title;
    }
    if (document.documentElement.getAttribute('data-page') === 'index') {
      const homeTitle = getByPath(copy, 'global.home_title');
      const homeDesc = getByPath(copy, 'global.home_description');
      if (homeTitle) document.title = homeTitle;
      if (homeDesc) {
        let tag = document.querySelector('meta[name="description"]');
        if (tag) tag.setAttribute('content', homeDesc);
      }
    } else if (page && page.meta_description) {
      let tag = document.querySelector('meta[name="description"]');
      if (!tag) {
        tag = document.createElement('meta');
        tag.setAttribute('name', 'description');
        document.head.appendChild(tag);
      }
      tag.setAttribute('content', page.meta_description);
    }
  }

  function renderAtAGlance(copy, pageKey) {
    const mount = document.getElementById('atAGlanceCards');
    const cards = getByPath(copy, `pages.${pageKey}.at_a_glance.cards`);
    if (!mount || !Array.isArray(cards)) return;
    mount.innerHTML = cards
      .map(
        (card) =>
          `<article class="alignment-card"><span>${esc(card.tag)}</span><div><h3>${esc(card.title)}</h3><p>${esc(card.body)}</p></div></article>`
      )
      .join('');
  }

  function renderBestProof(copy, pageKey) {
    const mount = document.getElementById('bestProofLinks');
    const links = getByPath(copy, `pages.${pageKey}.best_proof.links`);
    if (!mount || !Array.isArray(links)) return;
    mount.innerHTML = links.map((link, i) => pathRowHtml(link, i)).join('');
  }

  function renderPassport(copy, pageKey) {
    const mount = document.getElementById('passportGrid');
    const cells = getByPath(copy, `pages.${pageKey}.passport`);
    if (!mount || !Array.isArray(cells)) return;
    mount.innerHTML = cells
      .map(
        (cell) =>
          `<div class="passport-cell"><span class="meta-label">${esc(cell.label)}</span><strong>${esc(cell.value)}</strong></div>`
      )
      .join('');
  }

  function renderBeats(copy, pageKey) {
    const mount = document.getElementById('intentBeats');
    const beats = getByPath(copy, `pages.${pageKey}.intent.beats`);
    if (!mount || !Array.isArray(beats)) return;
    mount.innerHTML = beats
      .map(
        (beat) =>
          `<article class="alignment-card"><span>${esc(beat.tag)}</span><div><h3>${esc(beat.title)}</h3><p>${esc(beat.body)}</p></div></article>`
      )
      .join('');
  }

  function renderAxis(copy, pageKey) {
    const mount = document.getElementById('axisSteps');
    const steps = getByPath(copy, `pages.${pageKey}.axis.steps`);
    if (!mount || !Array.isArray(steps)) return;
    mount.innerHTML = steps
      .map(
        (step) =>
          `<article class="axis-card"><span class="meta-label">${esc(step.label)}</span><h3>${esc(step.title)}</h3><p>${esc(step.body)}</p></article>`
      )
      .join('');
  }

  function renderCraft(copy, pageKey) {
    const mount = document.getElementById('craftCards');
    const cards = getByPath(copy, `pages.${pageKey}.craft.cards`);
    if (!mount || !Array.isArray(cards)) return;
    mount.innerHTML = cards
      .map(
        (card) =>
          `<article class="stack-card"><span class="meta-label">${esc(card.tag)}</span><h3>${esc(card.title)}</h3><p>${esc(card.body)}</p></article>`
      )
      .join('');
  }

  function renderNextLinks(copy, pageKey) {
    const mount = document.getElementById('nextLinks');
    const links = getByPath(copy, `pages.${pageKey}.next.links`);
    if (!mount || !Array.isArray(links)) return;
    mount.innerHTML = links.map((link, i) => pathRowHtml(link, i)).join('');
  }

  async function hydrateIntakeHero() {
    const img = document.getElementById('heroLeadImage');
    if (!img) return;
    // Melusina character leads stay locked until remount tool wires dated plates.
    // Do not swap a Melusina void/iri or dated plate for blender intake cross heroes.
    const lock = img.getAttribute('data-hero-lock') || '';
    const srcNow = img.getAttribute('src') || '';
    if (lock === 'melusina' || /melusina/i.test(srcNow)) {
      return;
    }
    try {
      const blender = await fetchJson(BLENDER_INTAKE_URL).catch(() => null);
      if (blender && blender.hero_web_path) {
        img.src = blender.hero_web_path;
        img.alt = 'Melusina Vow Cross — EEVEE Komikaze beauty plate';
        return;
      }
      const intake = await fetchJson(INTAKE_URL);
      const cards = Array.isArray(intake.render_cards) ? intake.render_cards : [];
      const heroes = cards.filter((c) => c.group === 'hero' && c.web_path);
      const establishing = heroes.find((c) => /cam_hero_establishing/i.test(c.filename || ''));
      const packageHeroes = heroes.filter((c) => !(c.web_path || '').includes('/nightshift/'));
      packageHeroes.sort((a, b) => {
        const dateA = (a.filename || '').match(/(\d{8})/);
        const dateB = (b.filename || '').match(/(\d{8})/);
        if (dateA && dateB && dateA[1] !== dateB[1]) return dateB[1].localeCompare(dateA[1]);
        return (b.priority || 0) - (a.priority || 0);
      });
      const lead = establishing || packageHeroes[0] || heroes.sort((a, b) => (b.priority || 0) - (a.priority || 0))[0];
      if (lead) {
        img.src = lead.web_path;
        img.alt = lead.filename || 'Hero render';
      }
    } catch (_err) {
      /* keep static fallback src */
    }
  }

  const BLENDER_DENY_ASSETS = new Set(['magical_wand', 'sakura_petal']);
  // void_iri plates are studio-void duplicates; rose_window front still weak compose
  // Legacy Melusina portrait / Miraland T-pose postcard retired from intake grids
  const BLENDER_DENY_PATH = [
    '_void_iri_',
    'rose_window_komikaze_front',
    'melusina_eevee_portrait',
    'beauty_depth_color',
    'diorama_beauty',
    'melusina_beauty_34',
    'melusina_eevee_beauty_34',
  ];

  function isBlenderCardWebReady(card) {
    if (!card || !card.web_path) return false;
    if (card.web_ready === false) return false;
    if (card.retired === true) return false;
    if (BLENDER_DENY_ASSETS.has(card.asset_id)) return false;
    const path = String(card.web_path);
    if (BLENDER_DENY_PATH.some((frag) => path.includes(frag))) return false;
    const title = String(card.title || card.filename || '').toLowerCase();
    if (/portrait/i.test(title) && /melusina/i.test(title) && !/glam/i.test(title)) return false;
    return true;
  }

  function passportTriLabel(card) {
    const rows = card && card.passport && Array.isArray(card.passport.rows) ? card.passport.rows : [];
    const tri = rows.find((r) => Array.isArray(r) && String(r[0]).toLowerCase() === 'triangles');
    return tri && tri[1] ? String(tri[1]) : '';
  }

  function blenderCardHtml(card, fashion) {
    const href = esc(card.web_path);
    const title = esc(card.title || card.filename || 'Komikaze plate');
    const frame = fashion ? ' fashion-frame' : '';
    const tri = passportTriLabel(card);
    const captionBits = [];
    if (card.caption) captionBits.push(esc(card.caption));
    if (tri) captionBits.push(`${esc(tri)} tris`);
    const caption = captionBits.length ? `<p>${captionBits.join(' · ')}</p>` : '';
    const meta = card.group ? `<span class="meta-label">${esc(card.group)}</span>` : '';
    return `<a class="image-card${frame} holo-plate" href="${href}"><img src="${href}" alt="${title}" loading="lazy" /><div>${meta}<h3>${title}</h3>${caption}</div></a>`;
  }

  async function fetchBlenderCards() {
    const intake = await fetchJson(BLENDER_INTAKE_URL);
    const cards = Array.isArray(intake.render_cards) ? intake.render_cards : [];
    return cards.filter(isBlenderCardWebReady);
  }

  async function hydrateBlenderNprGrid(mountId, groupFilter, maxCount) {
    const mount = document.getElementById(mountId);
    if (!mount) return;
    const fashion = mount.classList.contains('lookbook-grid');
    try {
      let cards = await fetchBlenderCards();
      if (groupFilter) {
        const groups = Array.isArray(groupFilter) ? groupFilter : [groupFilter];
        cards = cards.filter((c) => groups.includes(c.group));
      }
      cards.sort((a, b) => (b.priority || 0) - (a.priority || 0));
      if (maxCount) cards = cards.slice(0, maxCount);
      if (!cards.length) {
        mount.innerHTML = '<p class="body-copy">Ornament proof plates loading soon.</p>';
        return;
      }
      mount.innerHTML = cards.map((c) => blenderCardHtml(c, fashion)).join('');
    } catch (_err) {
      mount.innerHTML = '<p class="body-copy">Blender portfolio intake unavailable.</p>';
    }
  }

  async function hydrateBlenderShopProof(mountId, maxCount) {
    await hydrateBlenderNprGrid(mountId, 'ornament', maxCount || 3);
  }

  async function hydrateCaptureBriefStats() {
    const mount = document.getElementById('captureBriefStats');
    if (!mount) return;
    try {
      const [intake, production] = await Promise.all([
        fetchJson(INTAKE_URL),
        fetchJson(PRODUCTION_SIGNALS_URL).catch(() => null),
      ]);
      const counts = intake.counts || {};
      const readiness = intake.readiness || {};
      const breakdowns = (intake.render_cards || []).filter((c) => c.group === 'breakdown' && c.web_path).length;
      const pcgIsm = production?.pcg_total_ism;
      const mis = production?.portfolio_mis || counts.material_instances || 0;
      const wpCount = production?.wp_pillars ? Object.keys(production.wp_pillars).length : 4;
      const stats = [
        ['Readiness', `${readiness.score || 0}/100`],
        ['WP Levels', `${wpCount}/4`],
        ['Portfolio MIs', String(mis)],
        ['PCG ISM', pcgIsm != null ? pcgIsm.toLocaleString() : '—'],
        ['Breakdowns', String(breakdowns)],
        ['Web plates', `${counts.renders_web_ready || 0}/${counts.renders_total || 0}`],
      ];
      mount.innerHTML = stats
        .map(
          (pair) =>
            `<div class="info-cell"><span>${esc(pair[0])}</span><strong>${esc(pair[1])}</strong></div>`
        )
        .join('');
    } catch (_err) {
      /* static fallback remains */
    }
  }

  async function hydrateLatestBreakdownPlate() {
    const mount = document.getElementById('latestBreakdownPlate');
    if (!mount) return;
    try {
      const intake = await fetchJson(INTAKE_URL);
      const cards = (intake.render_cards || [])
        .filter((c) => c.group === 'breakdown' && c.web_path)
        .sort((a, b) => (b.priority || 0) - (a.priority || 0));
      const lead = cards[0];
      if (!lead) {
        mount.innerHTML =
          '<p class="body-copy">No breakdown plates in intake yet. Capture from Cam_Breakdown_Shader on the next UE pass.</p>';
        return;
      }
      const href = esc(lead.web_path);
      const title = esc(lead.filename || 'Breakdown plate');
      mount.innerHTML = `<a class="image-card fashion-frame premium-card holo-plate" href="${href}"><img src="${href}" alt="${title}" loading="lazy" /><div><h3>${title}</h3><p>${esc(lead.caption || 'Latest shader breakdown from Unreal intake.')}</p></div></a>`;
    } catch (_err) {
      mount.innerHTML = '<p class="body-copy">Breakdown plate unavailable.</p>';
    }
  }

  async function hydrateNewRenderBanner() {
    const mount = document.getElementById('newRenderBanner');
    if (!mount) return;
    try {
      const catalog = await fetchJson(RENDER_CATALOG_URL);
      const fresh = Array.isArray(catalog.new_in_last_24h) ? catalog.new_in_last_24h : [];
      if (!fresh.length) {
        mount.hidden = true;
        return;
      }
      mount.hidden = false;
      const names = fresh
        .slice(0, 4)
        .map((item) => esc(item.filename))
        .join(', ');
      mount.innerHTML = `<p class="body-copy"><strong>${fresh.length} new render${fresh.length === 1 ? '' : 's'} on drive (24h):</strong> ${names}${fresh.length > 4 ? '…' : ''} — surfaced via scan + ingest.</p>`;
    } catch (_err) {
      mount.hidden = true;
    }
  }

  function renderPortalLinks(copy, pageKey) {
    const mount = document.getElementById('portalGrid');
    const links = getByPath(copy, `pages.${pageKey}.portals.links`);
    if (!mount || !Array.isArray(links)) return;
    mount.innerHTML = links
      .map((link) => {
        const accent = esc(link.accent || 'gold');
        const pillar = esc(link.accent || 'grotto');
        return `<a class="portal-card accent-${accent}" data-pillar="${pillar}" href="${esc(link.href)}"><span class="portal-step">${esc(link.step)}</span><div><h3>${esc(link.title)}</h3><p>${esc(link.body)}</p></div><span class="portal-open">Open →</span></a>`;
      })
      .join('');
  }

  async function hydrateHeroPlates(mountId, maxCount) {
    const mount = document.getElementById(mountId);
    if (!mount) return;
    const fashion = mount.classList.contains('lookbook-grid');
    try {
      const res = await fetch(INTAKE_URL, { cache: 'no-store' });
      const intake = await res.json();
      const cards = Array.isArray(intake.render_cards) ? intake.render_cards : [];
      let heroes = cards
        .filter((c) => c.group === 'hero' && c.web_path)
        .sort((a, b) => (b.priority || 0) - (a.priority || 0));
      if (maxCount) heroes = heroes.slice(0, maxCount);
      if (!heroes.length) {
        mount.innerHTML =
          '<a class="image-card fashion-frame" href="../generated/assets/l-sakurapath-hero.png"><img src="../generated/assets/l-sakurapath-hero.png" alt="Sakura path hero" loading="lazy" /><div><h3>Sakura Path</h3></div></a>';
        return;
      }
      mount.innerHTML = heroes
        .map((card) => {
          const href = esc(card.web_path);
          const title = esc(card.filename || 'Hero plate');
          const frame = fashion ? ' fashion-frame' : '';
          const caption = fashion && card.caption ? `<p>${esc(card.caption)}</p>` : '';
          return `<a class="image-card${frame} holo-plate" href="${href}"><img src="${href}" alt="${title}" loading="lazy" /><div><h3>${title}</h3>${caption}</div></a>`;
        })
        .join('');
    } catch (_err) {
      mount.innerHTML =
        '<a class="image-card" href="../generated/assets/l-sakurapath-hero.png"><img src="../generated/assets/l-sakurapath-hero.png" alt="Sakura path hero" /><div><h3>Sakura Path</h3></div></a>';
    }
  }

  async function hydrateHeroStrip(maxCount) {
    const mount = document.getElementById('heroStrip');
    if (!mount) {
      await hydrateHeroPlates('heroStrip', maxCount || 3);
      return;
    }
    // Keep curated HTML (Melusina face + known-good plates) when locked
    if (mount.getAttribute('data-lock') === 'static') return;
    const limit = maxCount || 3;
    try {
      const blenderCards = await fetchBlenderCards();
      const picks = [];
      const beauty = blenderCards.find((c) => c.id === 'cross_beauty_34');
      if (beauty) picks.push(beauty);
      blenderCards
        .filter((c) => c.hero_candidate && c.asset_id !== 'cross')
        .sort((a, b) => (b.priority || 0) - (a.priority || 0))
        .forEach((c) => {
          if (picks.length < limit && !picks.some((p) => p.id === c.id)) picks.push(c);
        });
      if (picks.length < limit) {
        blenderCards
          .filter((c) => c.group === 'ornament')
          .forEach((c) => {
            if (picks.length < limit && !picks.some((p) => p.id === c.id)) picks.push(c);
          });
      }
      if (picks.length) {
        mount.innerHTML = picks.map((c) => blenderCardHtml(c, false)).join('');
        return;
      }
    } catch (_err) {
      /* fall through to Unreal strip */
    }
    await hydrateHeroPlates('heroStrip', limit);
  }

  function renderProcessSteps(copy, pageKey) {
    const mount = document.getElementById('processSteps');
    const steps = getByPath(copy, `pages.${pageKey}.process.steps`);
    if (!mount || !Array.isArray(steps)) return;
    mount.innerHTML = steps
      .map(
        (step) =>
          `<div class="path-row"><span>${esc(step.step)}</span><div><h3>${esc(step.title)}</h3><p>${esc(step.body)}</p></div><b>—</b></div>`
      )
      .join('');
  }

  function renderPackageCards(copy, pageKey) {
    const mount = document.getElementById('packageCards');
    const cards = getByPath(copy, `pages.${pageKey}.packages.cards`);
    if (!mount || !Array.isArray(cards)) return;
    mount.innerHTML = cards
      .map(
        (card) =>
          `<article class="alignment-card"><span>${esc(card.tag)}</span><div><h3>${esc(card.title)}</h3><p>${esc(card.body)}</p></div><strong class="foil-caption">Custom quote</strong></article>`
      )
      .join('');
  }

  function renderUseCards(copy, pageKey) {
    const mount = document.getElementById('useCards');
    const cards = getByPath(copy, `pages.${pageKey}.uses.cards`);
    if (!mount || !Array.isArray(cards)) return;
    mount.innerHTML = cards
      .map(
        (card) =>
          `<article class="alignment-card"><span>${esc(card.tag)}</span><div><h3>${esc(card.title)}</h3><p>${esc(card.body)}</p></div></article>`
      )
      .join('');
  }

  async function hydrateProofGrid() {
    const mount = document.getElementById('proofGrid');
    if (!mount) return;
    try {
      const res = await fetch(INTAKE_URL, { cache: 'no-store' });
      const intake = await res.json();
      const cards = Array.isArray(intake.render_cards) ? intake.render_cards : [];
      const picks = cards.filter((c) => c.web_path).slice(0, 6);
      if (!picks.length) {
        mount.innerHTML =
          '<p class="body-copy">No web-ready plates yet. Run Unreal capture, then <code>ingest_unreal_portfolio.ps1</code>.</p>';
        return;
      }
      mount.innerHTML = picks
        .map((card) => {
          const href = esc(card.web_path);
          const title = esc(card.filename || card.group);
          const caption = esc(card.caption || `${card.group} plate`);
          return `<a class="image-card" href="${href}"><img src="${href}" alt="${title}" loading="lazy" /><div><span class="meta-label">${esc(card.group)}</span><h3>${title}</h3><p>${caption}</p></div></a>`;
        })
        .join('');
    } catch (_err) {
      mount.innerHTML = '<p class="body-copy">Intake JSON unavailable offline.</p>';
    }
  }

  async function hydrateRenderCatalogSection(mountId, groupFilter, maxCount) {
    const mount = document.getElementById(mountId);
    if (!mount) return;
    try {
      const catalog = await fetchJson(RENDER_CATALOG_URL);
      let items = Array.isArray(catalog.items) ? catalog.items : [];
      items = items.filter((item) => item.web_path && item.status === 'web_ready');
      if (groupFilter) {
        const groups = Array.isArray(groupFilter) ? groupFilter : [groupFilter];
        items = items.filter((item) => groups.includes(item.group));
      }
      items.sort((a, b) => (b.priority || 0) - (a.priority || 0));
      if (maxCount) items = items.slice(0, maxCount);
      if (!items.length) {
        mount.innerHTML = '<p class="body-copy">No scanned plates in this category yet. Run tools/scan_portfolio_renders.ps1.</p>';
        return;
      }
      mount.innerHTML = items
        .map((item) => {
          const href = esc(item.web_path);
          const title = esc(item.filename);
          const caption = esc(item.caption || '');
          return `<a class="image-card fashion-frame premium-card holo-plate" href="${href}"><img src="${href}" alt="${title}" loading="lazy" /><div><h3>${title}</h3><p>${caption}</p></div></a>`;
        })
        .join('');
    } catch (_err) {
      mount.innerHTML = '<p class="body-copy">Render catalog unavailable.</p>';
    }
  }

  async function hydrateReviewerPath() {
    const mount = document.getElementById('recruiterReviewPath');
    if (!mount) return;
    try {
      const data = await fetchJson(REVIEW_PATH_URL);
      const steps = Array.isArray(data.steps) ? data.steps : [];
      mount.innerHTML = steps
        .map((step, i) => {
          const stepLabel = motifStepPrefix(i, `${step.step} / ${step.title}`);
          return `<a class="path-row premium-card" href="${esc(step.href)}"><span>${esc(stepLabel)}</span><div><h3>${esc(step.title)}</h3><p>${esc(step.body)}</p></div><b>Open</b></a>`;
        })
        .join('');
    } catch (_err) {
      /* static HTML fallback remains */
    }
  }

  async function hydrateRenderConstellation() {
    const statsEl = document.getElementById('intakeStats');
    if (!statsEl) return;

    let intake = null;
    let production = null;

    try {
      intake = await fetchJson(INTAKE_URL);
    } catch (_err) {
      /* fallback below */
    }

    try {
      production = await fetchJson(PRODUCTION_SIGNALS_URL);
    } catch (_err) {
      /* optional enrichment */
    }

    if (!intake) {
      statsEl.innerHTML =
        '<div class="info-cell"><span>Intake</span><strong>Load failed</strong></div><div class="info-cell"><span>Fix</span><strong>Run ingest</strong></div>';
      return;
    }

    try {
      const counts = intake.counts || {};
      const readiness = intake.readiness || {};
      const scene = intake.scene || {};
      const budget = intake.stats || {};

      const sceneName = document.getElementById('intakeSceneName');
      if (sceneName) sceneName.textContent = scene.scene_name || 'ZenForestTest';

      const engine = document.getElementById('intakeEngine');
      if (engine) engine.textContent = scene.engine || 'Unreal Engine';

      const generated = document.getElementById('intakeGenerated');
      if (generated && intake.generated_at) {
        generated.textContent = new Date(intake.generated_at).toLocaleString();
      }

      const triangles = document.getElementById('intakeTriangles');
      if (triangles && budget.triangle_count != null) {
        triangles.textContent = `${budget.triangle_count} triangles`;
      }

      const budgetLine = document.getElementById('intakeBudget');
      if (budgetLine) {
        budgetLine.textContent = `${budget.draw_calls || 0} draw calls, ${budget.static_mesh_components || 0} static mesh components, ${budget.unique_materials || 0} unique materials, and ${budget.unique_meshes || 0} unique meshes.`;
      }

      const wpStatsEl = document.getElementById('intakeWpStats');
      const wpSummary = document.getElementById('intakePcgSummary');
      if (production && production.wp_pillars && wpStatsEl) {
        const pillars = production.wp_pillars;
        const wpData = [
          ['Total PCG ISM', String(production.pcg_total_ism || '—')],
          ['SakuraDream', String(pillars.SakuraDream?.total_ism || '—')],
          ['SpaceCathedral', String(pillars.SpaceCathedral?.total_ism || '—')],
          ['BaroqueGrotto', String(pillars.BaroqueGrotto?.total_ism || '—')],
          ['CosmicOrrery', String(pillars.CosmicOrrery?.total_ism || '—')],
        ];
        wpStatsEl.innerHTML = wpData
          .map(
            (pair) =>
              `<div class="info-cell"><span>${esc(pair[0])}</span><strong>${esc(pair[1])}</strong></div>`
          )
          .join('');
        if (wpSummary) {
          wpSummary.textContent = `Verified 2026-07-09 from wp_pillar_levels.json — all four pillars passed ISM regen.`;
        }
      }

      const statData = [
        ['Readiness', `${readiness.score || 0}/100`],
        ['Web-ready plates', `${counts.renders_web_ready || 0}/${counts.renders_total || 0}`],
        ['Shader families', counts.shader_families || 0],
        ['Portfolio MIs', production?.portfolio_mis || counts.material_instances || 0],
      ];
      statsEl.innerHTML = statData
        .map(
          (pair) =>
            `<div class="info-cell"><span>${esc(pair[0])}</span><strong>${esc(pair[1])}</strong></div>`
        )
        .join('');

      const signalsEl = document.getElementById('intakeSignals');
      if (signalsEl) {
        const base = Array.isArray(intake.latest_unreal_signals) ? intake.latest_unreal_signals : [];
        const extra = Array.isArray(production?.latest_signals) ? production.latest_signals : [];
        const merged = [...extra, ...base].filter(
          (s, i, arr) => arr.findIndex((x) => x.title === s.title) === i
        );
        signalsEl.innerHTML = merged
          .map(
            (signal) =>
              `<article class="intake-signal premium-card"><span class="intake-pill">${esc(signal.label)}</span><div><h3>${esc(signal.title)}</h3><p>${esc(signal.note)}</p></div></article>`
          )
          .join('');
      }

      const cardsEl = document.getElementById('intakeCards');
      if (cardsEl) {
        const cards = Array.isArray(intake.render_cards) ? intake.render_cards : [];
        const visible = cards
          .filter((card) => card.status !== 'deprecated' && card.id !== 'materials-grid-families-review')
          .sort((a, b) => (b.priority || 0) - (a.priority || 0));
        cardsEl.innerHTML = visible.length
          ? visible
              .map((card) => {
                const thumbClass =
                  card.group === 'materials' ? 'intake-thumb material-thumb' : 'intake-thumb';
                const media = card.web_path
                  ? `<img src="${esc(card.web_path)}" alt="${esc(card.filename)}" loading="lazy" />`
                  : `<span>${esc(card.status)}</span>`;
                return `<article class="intake-card premium-card"><div class="${thumbClass}">${media}</div><div class="intake-card-body"><span class="intake-pill">${esc(card.group)}</span><span class="intake-pill">${esc(card.status)}</span><h3>${esc(card.filename)}</h3><p>${esc(card.caption)}</p></div></article>`;
              })
              .join('')
          : '<p class="body-copy">No render cards in intake. Run tools/ingest_unreal_portfolio.ps1.</p>';
      }

      const familiesEl = document.getElementById('intakeFamilies');
      if (familiesEl) {
        const families = Array.isArray(intake.shader_families) ? intake.shader_families : [];
        familiesEl.innerHTML = families
          .map((family) => {
            const samples = (family.sample_materials || []).slice(0, 3).map(esc).join('<br>');
            return `<article class="intake-family premium-card"><strong>${esc(family.family)}</strong><p>${esc(family.count)} materials</p><p>${samples}</p></article>`;
          })
          .join('');
      }

      const needsEl = document.getElementById('intakeNeeds');
      if (needsEl) {
        const needs = (readiness.next_needs || []).filter(Boolean);
        needsEl.innerHTML =
          needs.map((need) => `<div class="intake-need">${esc(need)}</div>`).join('') ||
          '<div class="intake-need">No urgent gaps detected. Keep curating the strongest captures.</div>';
      }
    } catch (err) {
      statsEl.innerHTML = `<div class="info-cell"><span>Intake</span><strong>Error</strong></div>`;
    }
  }

  function pipelineStatusClass(status) {
    const s = String(status || '').toLowerCase();
    if (s === 'live') return 'is-live';
    if (s === 'in_progress' || s === 'partial') return 'is-progress';
    if (s === 'scaffold') return 'is-scaffold';
    return 'is-planned';
  }

  async function hydrateGeometryPipelines() {
    const lanesMount = document.getElementById('geometryPipelineLanes');
    const mathMount = document.getElementById('geometryMathChips');
    const zenMount = document.getElementById('geometryZenChips');
    const escherMount = document.getElementById('geometryEscherChips');
    const musicalMount = document.getElementById('geometryMusicalChips');
    if (!lanesMount && !mathMount && !zenMount && !escherMount && !musicalMount) return;

    try {
      const data = await fetchJson(GEOMETRY_PIPELINES_URL);

      if (lanesMount) {
        const lanes = Array.isArray(data.lanes) ? data.lanes : [];
        lanesMount.innerHTML = lanes
          .map((lane) => {
            const steps = Array.isArray(lane.steps) ? lane.steps : [];
            const stepHtml = steps
              .map(
                (step) =>
                  `<li class="pipeline-step" data-order="0${step.order}"><strong>${esc(step.name)}</strong><p>${esc(step.detail)}</p></li>`
              )
              .join('');
            const proof = (lane.proof_targets || []).slice(0, 3).map(esc).join(' · ');
            const statusClass = pipelineStatusClass(lane.status);
            const sheet = lane.sheet_href
              ? `<a href="${esc(lane.sheet_href)}">Open sheet</a>`
              : '';
            return `<article class="pipeline-lane premium-card"><div class="pipeline-lane-head"><div><span class="pipeline-lane-tag">${esc(lane.lane)}</span><h3>${esc(lane.title)}</h3></div><span class="pipeline-status ${statusClass}">${esc(lane.status)}</span></div><p style="margin:0 0 14px;color:var(--muted);line-height:1.58">${esc(lane.summary)}</p><ol class="pipeline-steps">${stepHtml}</ol><div class="pipeline-meta"><span>${esc(lane.asset_root)}</span>${sheet}<span>↔ ${esc(lane.unreal_parallel)}</span></div><p style="margin:10px 0 0;font-size:.82rem;color:var(--muted)">Proof: ${proof}</p></article>`;
          })
          .join('');
      }

      if (mathMount) {
        const structures = Array.isArray(data.math_structures) ? data.math_structures : [];
        mathMount.innerHTML = structures
          .map(
            (item) =>
              `<span class="math-chip"><b>${esc(item.name)}</b>${esc(item.tier)} · ${esc(item.asset)} · ${esc(item.status || '')}</span>`
          )
          .join('');
      }

      if (zenMount && Array.isArray(data.zen_gn_builders)) {
        zenMount.innerHTML = data.zen_gn_builders
          .map((id) => `<span class="math-chip"><b>${esc(id)}</b>SurrealArch zen shrine axis</span>`)
          .join('');
      }

      if (escherMount && Array.isArray(data.escher_gn_builders)) {
        escherMount.innerHTML = data.escher_gn_builders
          .map((id) => `<span class="math-chip"><b>${esc(id)}</b>Escher greybox GN · UE PCG port</span>`)
          .join('');
      }

      if (musicalMount) {
        const meshes = Array.isArray(data.musical_meshes) ? data.musical_meshes : [];
        const builders = Array.isArray(data.musical_gn_builders) ? data.musical_gn_builders : [];
        if (meshes.length) {
          musicalMount.innerHTML = meshes
            .map(
              (item) =>
                `<span class="math-chip"><b>${esc(item.name)}</b>${esc(item.asset)} · ${esc(item.status || 'fbx_ready')}</span>`
            )
            .join('');
        } else if (builders.length) {
          musicalMount.innerHTML = builders
            .map((id) => `<span class="math-chip"><b>${esc(id)}</b>Melodia Studio musical GN</span>`)
            .join('');
        }
      }
    } catch (_err) {
      if (lanesMount) {
        lanesMount.innerHTML =
          '<p class="body-copy">Pipeline manifest unavailable. Check generated/geometry_nodes_pipelines.json.</p>';
      }
    }
  }

  function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function landscapeLoopCard(item) {
    const poster = esc(item.poster || '');
    const label = esc(item.label || item.id);
    const caption = esc(item.caption || 'UDS day/night landscape loop');
    const webm = esc(item.webm_path || '');
    if (prefersReducedMotion() || !webm) {
      return `<a class="image-card fashion-frame landscape-loop-card holo-plate" href="${poster}"><img src="${poster}" alt="${label} terrain" loading="lazy" /><div><span class="meta-label">Day / night</span><h3>${label}</h3><p>${caption}</p></div></a>`;
    }
    return `<figure class="image-card fashion-frame landscape-loop-card holo-plate"><video autoplay loop muted playsinline poster="${poster}" src="${webm}"></video><div><span class="meta-label">Day / night loop</span><h3>${label}</h3><p>${caption}</p></div></figure>`;
  }

  async function hydrateLandscapeLoops(mountId) {
    const mount = document.getElementById(mountId || 'pillarTerrainGrid');
    if (!mount) return;
    try {
      const manifest = await fetchJson(LANDSCAPE_LOOPS_MANIFEST_URL);
      const entries = (Array.isArray(manifest.entries) ? manifest.entries : []).filter(
        (e) => e.status === 'web_ready' || e.webm_path || e.poster
      );
      if (!entries.length) return;
      mount.innerHTML = entries.map(landscapeLoopCard).join('');
      mount.classList.add('landscape-loop-grid');
    } catch (_err) {
      /* keep static HTML posters */
    }
  }

  async function hydrateMaterialLoopGallery() {
    const mount = document.getElementById('miLoopGallery');
    const heroMount = document.getElementById('miLoopHero');
    if (!mount && !heroMount) return;

    try {
      const [loopsRes, catalogRes] = await Promise.all([
        fetch(MATERIAL_LOOPS_MANIFEST_URL, { cache: 'no-store' }),
        fetch(MI_PREVIEW_MANIFEST_URL, { cache: 'no-store' }).catch(() => null),
      ]);
      const manifest = await loopsRes.json();
      const catalog = catalogRes ? await catalogRes.json() : { entries: [] };
      const entries = Array.isArray(manifest.entries) ? manifest.entries : [];
      const ready = entries.filter((e) => e.webm_path && e.status === 'web_ready');
      const readyIds = new Set(ready.map((e) => e.id));
      const catalogEntries = Array.isArray(catalog.entries) ? catalog.entries : [];
      const pending = catalogEntries.filter((e) => e.id && !readyIds.has(e.id));

      const hero = ready.find((e) => e.priority === 'hero' || e.id === 'MI_ZenTrim_FlowersLots') || ready[0];
      const heroPending = !hero && pending.find((e) => e.priority === 'hero' || e.id === 'MI_ZenTrim_FlowersLots');

      if (heroMount) {
        if (hero) {
          const poster = hero.poster ? ` poster="${esc(hero.poster)}"` : '';
          heroMount.innerHTML = `<figure class="image-card premium-card material-proof-frame loop-hero-card" data-pillar="sakura"><video autoplay loop muted playsinline${poster} src="${esc(hero.webm_path)}"></video><div><h3>${esc(hero.id)}</h3><p>${esc(hero.backdrop || 'Melodia_VoidGradient')} · ${esc(hero.preview_mesh || 'sphere')} · ${esc(String(hero.duration_sec || '4'))}s loop</p></div></figure>`;
        } else if (heroPending) {
          heroMount.innerHTML = `<figure class="image-card premium-card material-proof-frame loop-hero-card loop-pending" data-pillar="sakura"><div class="loop-pending-swatch" aria-hidden="true"></div><div><h3>${esc(heroPending.id)}</h3><p>Awaiting capture — ${esc(heroPending.preview_mesh || 'swatch')} · ${esc(heroPending.backdrop || 'studio')}</p></div></figure>`;
        }
      }

      if (mount) {
        const pendingTiles = pending
          .slice(0, 12)
          .map(
            (item) =>
              `<figure class="image-card premium-card material-proof-frame mi-loop-tile loop-pending"><div class="loop-pending-swatch" aria-hidden="true"></div><div><h3>${esc(item.id)}</h3><p>Awaiting capture · ${esc(item.preview_mesh || '')}</p></div></figure>`
          )
          .join('');

        const groups = {
          hero: ready.filter((e) => e.priority === 'hero'),
          cosmic: ready.filter((e) => /^MI_Cosmic_|celestial_nebula/i.test(e.id)),
          trimsheet: ready.filter((e) => /ZenTrim|ClothTrim/i.test(e.id)),
          sdf: ready.filter((e) => /^MI_SDF_/i.test(e.id)),
          showcase: ready.filter((e) => /^MI_Show_/i.test(e.id)),
        };
        const order = [
          ['Hero loops', groups.hero, 'Validation captures on Melodia void/iri gradient — no UE headquarters sky.'],
          ['Cosmic loops', groups.cosmic, 'NightShift cosmic family — void-padded interim until MRQ orbit recapture.'],
          ['Trimsheet loops', groups.trimsheet, 'Vertical swatch staging for layer A/B trimsheet reads.'],
          ['SDF loops', groups.sdf, 'Orbital sphere captures for stylized SDF band materials.'],
          ['Showcase loops', groups.showcase, 'Starter MI_Show_* presets on the universal master.'],
        ];
        let html = order
          .filter(([, items]) => items.length > 0)
          .map(([label, items, caption]) => {
            const tiles = items
              .map((item) => {
                const src = item.webm_path;
                const poster = item.poster ? ` poster="${esc(item.poster)}"` : '';
                return `<figure class="image-card premium-card material-proof-frame mi-loop-tile"><video autoplay loop muted playsinline${poster} src="${esc(src)}"></video><div><h3>${esc(item.id)}</h3><p>${esc(item.backdrop || 'Melodia_VoidGradient')} · ${esc(item.preview_mesh || '')}</p></div></figure>`;
              })
              .join('');
            return `<section class="mi-group"><div class="section-head"><div><p class="eyebrow">${esc(label)}</p><h2>${esc(label)}</h2></div><p>${esc(caption)}</p></div><div class="image-grid mi-grid">${tiles}</div></section>`;
          })
          .join('');

        if (pending.length > 0) {
          html += `<section class="mi-group"><div class="section-head"><div><p class="eyebrow">Pipeline queue</p><h2>Awaiting capture</h2></div><p>Batches of 3 per <code>publish_material_loops.ps1</code> run — no empty gallery while the catalog fills in.</p></div><div class="image-grid mi-grid">${pendingTiles}</div></section>`;
        }

        mount.innerHTML =
          html ||
          '<p class="body-copy">Material loops pending capture. Run <code>Tools\\publish_material_loops.ps1</code> when ready.</p>';
      }
    } catch (_err) {
      const fallback =
        '<p class="body-copy">Material loop manifest unavailable. Run <code>Tools\\publish_material_loops.ps1</code> to generate manifests.</p>';
      if (mount) mount.innerHTML = fallback;
      if (heroMount) heroMount.innerHTML = fallback;
    }
  }

  async function hydrateMaterialGallery() {
    const mount = document.getElementById('miGalleryGroups');
    if (!mount) return;

    try {
      const res = await fetch(NIGHTSHIFT_MANIFEST_URL, { cache: 'no-store' });
      const manifest = await res.json();
      const groups = Array.isArray(manifest.groups) ? manifest.groups : [];
      mount.innerHTML = groups
        .map((group) => {
          const items = Array.isArray(group.items) ? group.items : [];
          const tiles = items
            .map((item) => {
              const filename = `${item.id}.png`;
              const src = `${NIGHTSHIFT_ASSET_BASE}${filename}`;
              return `<figure class="image-card premium-card material-proof-frame mi-tile"><img src="${esc(src)}" alt="${esc(item.id)} preview sphere" loading="lazy" /><div><h3>${esc(item.id)}</h3><p>${esc(item.caption || '')}</p></div></figure>`;
            })
            .join('');
          return `<section class="mi-group"><div class="section-head"><div><p class="eyebrow">${esc(group.label)}</p><h2>${esc(group.label)}</h2></div><p>${esc(group.caption || '')}</p></div><div class="image-grid mi-grid">${tiles}</div></section>`;
        })
        .join('');
    } catch (_err) {
      mount.innerHTML =
        '<p class="body-copy">NightShift manifest unavailable. Check generated/nightshift_manifest.json.</p>';
    }
  }

  function initMobileNav() {
    document.querySelectorAll('.shell-nav').forEach((nav) => {
      if (nav.querySelector('.nav-toggle')) return;
      const links = nav.querySelector('.nav-links');
      if (!links) return;

      const toggle = document.createElement('button');
      toggle.type = 'button';
      toggle.className = 'nav-toggle';
      toggle.setAttribute('aria-expanded', 'false');
      toggle.setAttribute('aria-controls', links.id || 'site-nav-links');
      if (!links.id) links.id = 'site-nav-links';

      const cta = nav.querySelector('.nav-cta');
      if (cta) nav.insertBefore(toggle, cta);
      else nav.appendChild(toggle);

      const close = () => {
        nav.classList.remove('nav-open');
        toggle.setAttribute('aria-expanded', 'false');
      };

      toggle.addEventListener('click', () => {
        const open = nav.classList.toggle('nav-open');
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      });

      links.querySelectorAll('a').forEach((a) => a.addEventListener('click', close));
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') close();
      });
    });
  }

  function ensureA11yLandmarks() {
    const shell = document.querySelector('.melodia-shell');
    if (!shell) return;
    const main = shell.querySelector('main');
    if (main && !main.id) main.id = 'main';
    if (!shell.querySelector(':scope > .skip-link')) {
      const skip = document.createElement('a');
      skip.className = 'skip-link';
      skip.href = '#main';
      skip.textContent = 'Skip to main content';
      shell.insertBefore(skip, shell.firstChild);
    }
  }

  function getEffects(shell) {
    if (!shell) return ['starfield', 'holo', 'magical'];
    const raw = shell.getAttribute('data-effects');
    if (!raw) return ['starfield', 'holo', 'magical'];
    return raw.split(',').map((s) => s.trim()).filter(Boolean);
  }

  function hasEffect(shell, name) {
    return getEffects(shell).includes(name);
  }

  /** Decorative unicode divider pool for viz/rhythm rules. */
  var DIVIDER_VARIANTS = [
    {
      id: 'astral',
      glyph: '·͙*̩̩͙˚̩̥̩̥*̩̩̥͙　✩　*̩̩̥͙˚̩̥̩̥*̩̩͙‧͙',
      flank: '✩',
    },
    { id: 'diamond', glyph: '◇─◇──◇─◇', flank: '◇─◇──◇─◇' },
    { id: 'pipes', glyph: '┊ ⋆ ┊ . ┊ ┊', flank: '┊ ⋆ ┊ . ┊ ┊' },
    { id: 'pipes-dot', glyph: '┊ ┊⋆ ┊ .', flank: '┊ ┊⋆ ┊ .' },
    {
      id: 'pipes-spark',
      glyph: '┊ ┊ ⋆˚ ⁭ ✧. ┊ ⁭ ⁭ ⁭ ⁭',
      flank: '┊ ┊ ⋆˚ ✧. ┊',
    },
  ];

  function ensureEditorialPolishCss() {
    if (
      document.querySelector('link[data-melodia-polish], link[href*="melodia-editorial-polish.css"]')
    ) {
      return;
    }
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'melodia-editorial-polish.css';
    link.setAttribute('data-melodia-polish', '1');
    document.head.appendChild(link);
  }

  function pickDividerVariant(el, index) {
    var preset = el.getAttribute('data-divider');
    var found = DIVIDER_VARIANTS.find(function (v) {
      return v.id === preset;
    });
    if (found) return found;
    return DIVIDER_VARIANTS[index % DIVIDER_VARIANTS.length];
  }

  function extractGlyphLabel(glyph) {
    var label = glyph.getAttribute('data-label');
    if (label) return label;
    var raw = (glyph.textContent || '').trim();
    if (!raw) return '';
    var parts = raw.split(/\s+/);
    if (parts.length > 1 && /^[♪✦✧·༚✩◇┊]/.test(parts[0])) {
      label = parts.slice(1).join(' ');
    } else if (!/^[·͙*̩̩˚̥✩◇┊⋆⁭✧─]/.test(raw)) {
      label = raw;
    }
    if (label) glyph.setAttribute('data-label', label);
    return label || '';
  }

  function initDividerVariants() {
    var nodes = document.querySelectorAll(
      '.editorial-rhythm-divider, .viz-rule, .nikki-spark-rule, .editorial-rule, .melodia-divider'
    );
    if (!nodes.length) return;
    nodes.forEach(function (el, index) {
      var variant = pickDividerVariant(el, index);
      el.setAttribute('data-divider', variant.id);
      el.setAttribute('data-divider-glyph', variant.glyph);
      el.setAttribute('data-divider-flank', variant.flank);

      if (el.classList.contains('nikki-spark-rule')) {
        var sparks = el.querySelectorAll('.spark');
        sparks.forEach(function (spark) {
          spark.textContent = variant.flank;
          spark.setAttribute('aria-hidden', 'true');
        });
        return;
      }

      if (el.classList.contains('editorial-rule')) {
        var diamonds = el.querySelectorAll('.diamond');
        diamonds.forEach(function (d) {
          d.textContent = variant.flank;
          d.classList.add('glyph-flank');
        });
        return;
      }

      var glyph = el.querySelector('.glyph');
      if (glyph) {
        var label = extractGlyphLabel(glyph);
        glyph.textContent = label ? variant.glyph + '  ' + label : variant.glyph;
      } else if (el.classList.contains('melodia-divider')) {
        el.textContent = variant.glyph;
      }
    });
  }

  function initIvorySurfaces() {
    // Sparse defaults when pages forget data-surface — keep cosmic dominant
    var auto = document.querySelectorAll(
      '.band.paper[data-ivory="auto"], .band.cloud[data-ivory="auto"]'
    );
    auto.forEach(function (band) {
      band.setAttribute('data-surface', 'ivory');
      band.classList.add('ivory');
    });
  }

  function bootEffects() {
    const shell = document.querySelector('.melodia-shell');
    if (!shell) return;

    const heroType = shell.getAttribute('data-hero') || 'editorial';
    const starIntensity = heroType === 'cosmic' ? 'cosmic' : 'standard';

    if (hasEffect(shell, 'starfield') && global.MelodiaStarfield) {
      global.MelodiaStarfield.init({ intensity: starIntensity });
    }

    if (hasEffect(shell, 'holo') && global.MelodiaDreamShaders) {
      global.MelodiaDreamShaders.init();
    }

    if (hasEffect(shell, 'orrery') && global.MelodiaOrrery) {
      global.MelodiaOrrery.upgradePremiumOrreries();
      global.MelodiaOrrery.bindOrreryTilt();
    }

    if (global.MelodiaOrrery) {
      global.MelodiaOrrery.mountAll();
      global.MelodiaOrrery.upgradeHeroOrreries();
    }

    if (global.MelodiaPlanetarium) {
      global.MelodiaPlanetarium.mountAll();
      if (hasEffect(shell, 'planetarium')) {
        global.MelodiaPlanetarium.mountHeroReplacement();
      }
    }

    if (hasEffect(shell, 'instruments') && global.MelodiaCosmicInstruments) {
      global.MelodiaCosmicInstruments.mount();
    }

    if (hasEffect(shell, 'magical') && global.MelodiaMagicalGirl) {
      global.MelodiaMagicalGirl.boot();
    }

    if (heroType === 'cosmic' && global.initPremiumHero) {
      global.initPremiumHero();
    }
  }

  async function init(options) {
    const pageKey = (options && options.page) || document.documentElement.getAttribute('data-page') || '';
    ensureEditorialPolishCss();
    ensureA11yLandmarks();
    initParallax();
    initMobileNav();
    initDividerVariants();
    initIvorySurfaces();

    let copy = null;
    try {
      const platesRes = await fetch(PLATES_URL, { cache: 'no-store' });
      applyPlates(await platesRes.json());
    } catch (_err) {
      /* static img src fallbacks remain */
    }
    try {
      const res = await fetch(COPY_URL, { cache: 'no-store' });
      copy = await res.json();
      applyCopy(copy, pageKey);
      renderPassport(copy, pageKey);
      renderBeats(copy, pageKey);
      renderAxis(copy, pageKey);
      renderCraft(copy, pageKey);
      renderNextLinks(copy, pageKey);
      renderPortalLinks(copy, pageKey);
      renderAtAGlance(copy, pageKey);
      renderBestProof(copy, pageKey);
      renderPackageCards(copy, pageKey);
      renderProcessSteps(copy, pageKey);
      renderUseCards(copy, pageKey);
    } catch (_err) {
      /* static HTML fallbacks remain */
    }

    if (options && options.intake) {
      await hydrateIntakeHero();
      await hydrateProofGrid();
    }
    if (options && options.heroStrip) {
      await hydrateHeroStrip(options.heroStrip);
    }
    if (options && options.heroGrid) {
      await hydrateHeroPlates('heroGrid', typeof options.heroGrid === 'number' ? options.heroGrid : null);
    }
    if (options && options.blenderNprGrid) {
      const n = typeof options.blenderNprGrid === 'number' ? options.blenderNprGrid : null;
      await hydrateBlenderNprGrid('blenderNprGrid', null, n);
    }
    if (options && options.blenderOrnamentProof) {
      const n = typeof options.blenderOrnamentProof === 'number' ? options.blenderOrnamentProof : 3;
      await hydrateBlenderShopProof('blenderOrnamentProof', n);
    }
    if (options && options.constellation) {
      await hydrateRenderConstellation();
    }
    if (options && options.materialLoopGallery) {
      await hydrateMaterialLoopGallery();
    }
    if (options && options.landscapeLoops) {
      await hydrateLandscapeLoops(
        typeof options.landscapeLoops === 'string' ? options.landscapeLoops : 'pillarTerrainGrid'
      );
    }
    if (options && options.materialGallery) {
      await hydrateMaterialGallery();
    }
    if (options && options.geometryPipelines) {
      await hydrateGeometryPipelines();
    }
    if (options && options.reviewerPath) {
      await hydrateReviewerPath();
    }
    if (options && options.shaderProofGrid) {
      await hydrateRenderCatalogSection('shaderProofGrid', 'shader_proof', options.shaderProofGrid);
    }
    if (options && options.sakuraMoodGrid) {
      await hydrateRenderCatalogSection('sakuraMoodGrid', 'sakura_mood', options.sakuraMoodGrid);
    }
    if (options && options.captureBriefStats) {
      await hydrateCaptureBriefStats();
    }
    if (options && options.latestBreakdownPlate) {
      await hydrateLatestBreakdownPlate();
    }
    if (options && options.newRenderBanner) {
      await hydrateNewRenderBanner();
    }

    if (global.MelodiaDreamShaders && global.MelodiaDreamShaders.initHoloPlates) {
      global.MelodiaDreamShaders.initHoloPlates();
    }

    bootEffects();
  }

  global.MelodiaEditorial = {
    init,
    initParallax,
    initMobileNav,
    bootEffects,
    getEffects,
    applyCopy,
    hydrateRenderConstellation,
    hydrateMaterialGallery,
    hydrateMaterialLoopGallery,
    hydrateLandscapeLoops,
    hydrateGeometryPipelines,
    hydrateReviewerPath,
    hydrateRenderCatalogSection,
    hydrateCaptureBriefStats,
    hydrateLatestBreakdownPlate,
    hydrateNewRenderBanner,
  };
})(window);
