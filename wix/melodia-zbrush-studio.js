/**
 * Melodia ZBrush Sculpt Studio — High-Poly Ornamental & Retopology Inspector
 */
(function (global) {
  'use strict';

  // Default selected = first entry. Melusina clay sculpts are the only clean plates;
  // all zenlantern_* / melody_* komikaze beauty_* plates have broken purple AO noise.
  var SCULPTS = [
    {
      id: 'melusina_head',
      name: 'Melusina Bust & Jewelry',
      image: '../generated/assets/sculpt/sculpt_melusina_three_quarter.png',
      fallback: '../generated/assets/sculpt/sculpt_melusina_profile.png',
      polycount: 'Hero Mesh · 68K Low-Poly Quad',
      tools: 'Maya Retopology / ZBrush Detailing',
      notes: 'Stylized facial planar transitions with Subdivision surface support and water-hair attachment curve flow.'
    },
    {
      id: 'melody_tokens',
      name: 'Melody Token Quartet',
      image: '../generated/assets/sculpt/sculpt_melodytoken_swirl.png',
      fallback: '../generated/assets/sculpt/sculpt_melodytoken_star.png',
      polycount: '4-Piece Set · 450K Triangles',
      tools: 'ZBrush Boolean DynaMesh + QuadRemesher',
      notes: 'Four musical-celestial motifs (Star, Swirl, Heart, Water) sculpted for physics drop pickups.'
    },
    {
      id: 'zen_lantern',
      name: 'Zen Lantern (High-Poly)',
      image: '../generated/assets/sculpt/sculpt_zenlantern_three_quarter.png',
      fallback: '../generated/assets/sculpt/sculpt_zenlantern_front.png',
      polycount: '1.8M Polys (SubD Level 5)',
      tools: 'ZBrush / 3DCoat / Blender Retopo',
      notes: 'Curved pagoda eaves, filigree lattice perforations, soft-edge bevels for Komikaze Toon normals.'
    },
  ];

  function init(containerSelector) {
    var root = document.querySelector(containerSelector || '#zbrush-studio-mount');
    if (!root) return;

    var activeIndex = 0;
    var currentPass = 'primary'; // 'primary' | 'alternate'

    function render() {
      var item = SCULPTS[activeIndex];
      var currentSrc = currentPass === 'alternate' ? item.fallback : item.image;

      root.innerHTML = `
        <div class="zbrush-studio-container">
          <div class="zbrush-viewport">
            <img id="zbrush-viewport-img" src="${currentSrc}" alt="${item.name}" onerror="this.onerror=null; this.src='${currentPass === 'alternate' ? item.image : item.fallback}';" />
          </div>

          <div class="zbrush-studio-sidebar">
            <div class="zbrush-asset-list" role="tablist" aria-label="Sculpt Models">
              ${SCULPTS.map((s, idx) => `
                <button type="button" 
                        class="zbrush-asset-item ${idx === activeIndex ? 'active' : ''}" 
                        data-index="${idx}"
                        role="tab"
                        aria-selected="${idx === activeIndex ? 'true' : 'false'}">
                  <span aria-hidden="true">✦</span>
                  <strong>${s.name}</strong>
                </button>
              `).join('')}
            </div>

            <div class="zbrush-pass-toggle" role="group" aria-label="Sculpt View Passes">
              <button type="button" 
                      class="zbrush-pass-btn ${currentPass === 'primary' ? 'active' : ''}" 
                      data-pass="primary"
                      aria-pressed="${currentPass === 'primary' ? 'true' : 'false'}">Primary View</button>
              <button type="button" 
                      class="zbrush-pass-btn ${currentPass === 'alternate' ? 'active' : ''}" 
                      data-pass="alternate"
                      aria-pressed="${currentPass === 'alternate' ? 'true' : 'false'}">Angle / Alternate</button>
            </div>

            <div class="zbrush-passport-sheet">
              <h4>Sculpt Technical Passport</h4>
              <div class="zbrush-passport-row">
                <span>Density</span>
                <strong>${item.polycount}</strong>
              </div>
              <div class="zbrush-passport-row">
                <span>Pipeline</span>
                <strong>${item.tools}</strong>
              </div>
              <div class="zbrush-passport-row" style="flex-direction:column;gap:4px;padding-top:8px;border:none;">
                <span>Artistic &amp; Technical Notes</span>
                <p style="margin:0;color:var(--color-text-secondary);font-size:0.75rem;line-height:1.5;">${item.notes}</p>
              </div>
            </div>
          </div>
        </div>
      `;

      root.querySelectorAll('[data-index]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          activeIndex = parseInt(btn.getAttribute('data-index'), 10);
          render();
        });
      });

      root.querySelectorAll('[data-pass]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          currentPass = btn.getAttribute('data-pass');
          render();
        });
      });
    }

    render();
  }

  global.MelodiaZBrushStudio = { init: init, SCULPTS: SCULPTS };
})(window);
