# Complete Integration Workflow: Unreal Pipeline → GitHub → Wix

Complete end-to-end workflow for automatically generating portfolio graphics in Unreal and deploying them to your Wix website via GitHub Pages.

> **Repo status (2026-08-05):** `BS_GodFile/.git` is healthy at repo root on `main`; latest local commit `ec20b015`; checkpoint `6154cc1e` captures recovered history. Push to `origin` is currently blocked by network connectivity to `github.com:443`. Collaborator environment scripts added under `deploy/`.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                       BLENDER 5.1 (Procedural Geometry)             │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  Surreal Architecture Generator                                │ │
│  │  - Style genomes & grammar                                     │ │
│  │  - Greybox layout                                              │ │
│  │  - World export (.world.json)                                  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │ OSC / Live Link / Spout
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       TOUCHDESIGNER 2025+ (Real-Time Interaction)    │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  Real-Time FX & Audio Layer                                    │ │
│  │  - Audio analysis (Melusina VoiceSynth → CHOPs)                │ │
│  │  - Shader prototyping (GLSL TOPs)                              │ │
│  │  - Particle systems (POPs)                                     │ │
│  │  - OSC routing hub (TD ↔ Blender ↔ UE)                         │ │
│  │  - Interactive portfolio viewer                                │ │
│  │  - Embody/Envoy MCP server (53 tools, localhost:9870)          │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │ OSC / Spout / NDI / TouchEngine
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        UNREAL ENGINE 5.8                            │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Portfolio Pipeline (generate_portfolio.py)                   │  │
│  │  - Scene metadata extraction                                 │  │
│  │  - Render capture (viewport + Monolith)                        │  │
│  │  - Material previews                                         │  │
│  │  - Statistics aggregation                                     │  │
│  │  - Package compilation                                        │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Web Component Generator (web_component_generator.py)        │  │
│  │  - Theme detection (environment/character/prop/abstract)        │  │
│  │  - Performance analysis (high/balanced/highQuality)            │  │
│  │  - Hero config generation                                     │  │
│  │  - Passport config generation                                 │  │
│  │  - Effect config generation (aurora/cosmic)                    │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  GitHub Deployer (github_deployer.py)                         │  │
│  │  - Clone/update GitHub repository                             │  │
│  │  - Sync modular components                                    │  │
│  │  - Generate project HTML files                                │  │
│  │  - Commit and push changes                                    │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GITHUB PAGES (Static Hosting)                     │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  username.github.io/wix-portfolio-assets/                     │  │
│  │  - components/ (modular library)                               │  │
│  │  - projects/ (example implementations)                        │  │
│  │  - generated/ (auto-generated from Unreal)                     │  │
│  │  - deployment-manifest.json (current deployment info)          │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        WIX WEBSITE                                   │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Iframe Integration                                            │  │
│  │  - Dynamic loading from deployment manifest                   │  │
│  │  - Automatic updates from pipeline                            │  │
│  │  - Fallback mechanisms                                         │  │
│  │  - Performance optimization                                    │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────┐
                    │  UNIFIED MCP ORCHESTRATION   │
                    │  Embody + Monolith + Blender │
                    │  (Single AI session)         │
                    └─────────────────────────────┘
```

---

## Quick Start Workflow

### Step 1: Initial Setup (One-Time)

#### 1.1 Create GitHub Repository
1. Create new repository: `wix-portfolio-assets`
2. Enable GitHub Pages (Settings → Pages → Source: main branch)
3. Clone repository locally: `git clone https://github.com/username/wix-portfolio-assets.git`

#### 1.2 Upload Modular Components
1. Copy components from `_staging/design-system/components/` to repository `components/`
2. Copy examples from `_staging/design-system/examples/` to repository `projects/`
3. Create index.html in repository root
4. Commit and push: `git add . && git commit -m "Initial components" && git push origin main`

#### 1.3 Configure Unreal Pipeline
1. Create `Saved/Portfolio/WebComponents/deployment_config.json` in Unreal project
2. Add GitHub repository URL and authentication
3. Test Git connection from Unreal environment

#### 1.4 Integrate with Wix
1. Add iframe embed to Wix site
2. Implement dynamic loading script
3. Test with static GitHub Pages URL
4. Verify fallback mechanisms work

### Step 2: Automatic Deployment (Ongoing)

#### 2.1 Run Portfolio Pipeline in Unreal
```python
# In Unreal Editor Python console
py Content/Python/generate_portfolio.py
```

This automatically:
- Generates portfolio package
- Creates web component configurations
- Deploys to GitHub (if enabled)
- Updates deployment manifest

#### 2.2 Wix Auto-Updates
The iframe loading script automatically:
- Checks deployment manifest every 5 minutes
- Loads latest component configurations
- Applies fallbacks if GitHub is unavailable
- Optimizes based on device type

---

## Detailed Workflow

### Phase 1: Unreal Pipeline Execution

> **TouchDesigner Integration:** As of `feature/touchdesigner-mcp-integration`, the pipeline now includes a TouchDesigner real-time layer between Blender and Unreal Engine. See `Docs/TOUCHDESIGNER_MCP_INTEGRATION_PLAN.md` for the full architecture. TD handles audio reactivity, shader prototyping, and MCP orchestration unification.

#### 1.1 Scene Metadata Extraction
**Script:** `scene_metadata_exporter.py`

**Input:** Active Unreal level  
**Output:** `Saved/Portfolio/Metadata/scene_metadata.json`

**Process:**
1. Load active level
2. Scan for static mesh actors
3. Extract material assignments
4. Capture level metadata
5. Write JSON manifest

#### 1.2 Render Capture
**Script:** `capture_portfolio_renders.py`

**Input:** Scene metadata  
**Output:** PNG renders in `Saved/Portfolio/Renders/`

**Process:**
1. Execute viewport capture for hero renders
2. Execute Monolith captures for materials/breakdowns
3. Organize output files
4. Compile renders manifest

#### 1.3 Package Compilation
**Script:** `portfolio_aggregator.py`

**Input:** All JSON manifests  
**Output:** `Saved/Portfolio/portfolio_package.json`

**Process:**
1. Load all source manifests
2. Validate against schema
3. Merge into unified package
4. Add validation warnings
5. Write final package

### Phase 2: Web Component Generation

#### 2.1 Theme Detection
**Script:** `web_component_generator.py`

**Logic:**
```python
def detect_content_theme(package):
    assets = package.get('assets', [])
    scene = package.get('scene', {})
    
    # Analyze asset types and scene content
    character_count = count_character_assets(assets)
    environment_count = count_environment_assets(assets)
    
    # Return appropriate theme
    if character_count > threshold:
        return 'character'
    elif environment_count > threshold:
        return 'environment'
    else:
        return 'abstract'
```

#### 2.2 Performance Analysis
**Logic:**
```python
def select_performance_level(package):
    stats = package.get('stats', {})
    triangle_count = stats.get('triangle_count', 0)
    
    if triangle_count > 1000000:
        return 'high'  # Minimal effects
    elif triangle_count > 500000:
        return 'balanced'  # Default
    else:
        return 'highQuality'  # Maximum effects
```

#### 2.3 Configuration Generation
**Output Files:**
- `hero_config.json` - Hero banner configuration
- `passport_config.json` - Asset passport configuration
- `effect_config.json` - Special effects configuration
- `deployment_manifest.json` - Wix deployment manifest

### Phase 3: GitHub Deployment

#### 3.1 Repository Synchronization
**Script:** `github_deployer.py`

**Process:**
1. Clone/update local GitHub repository
2. Copy modular components from design system
3. Copy generated configuration files
4. Generate project-specific HTML files
5. Commit and push changes

#### 3.2 HTML Generation
**Function:** `generate_project_html_from_config()`

**Process:**
1. Load component configuration
2. Build HTML using modular components
3. Include required CSS/JS files
4. Apply configuration parameters
5. Write to `generated/` directory

### Phase 4: Wix Integration

#### 4.1 Initial Setup
**Add to Wix Site:**
```html
<div id="melodia-hero-container"></div>
<script>
// Dynamic loading script
fetch('https://username.github.io/wix-portfolio-assets/generated/deployment-manifest.json')
  .then(response => response.json())
  .then(manifest => {
    // Load component from manifest
    loadComponent(manifest.assets.hero);
  });
</script>
```

#### 4.2 Automatic Updates
**Mechanism:**
- Polling every 5 minutes
- Check deployment manifest version
- Reload if version changed
- Apply fallback if GitHub unavailable

---

## File Changes Summary

### New Files in Unreal Project

```
Content/Python/
├── web_component_generator.py (NEW)
├── github_deployer.py (NEW)
└── generate_portfolio.py (UPDATED)

Saved/Portfolio/
├── WebComponents/ (NEW DIRECTORY)
│   ├── deployment_config.json (NEW)
│   ├── hero_config.json (AUTO-GENERATED)
│   ├── passport_config.json (AUTO-GENERATED)
│   ├── effect_config.json (AUTO-GENERATED)
│   └── deployment_manifest.json (AUTO-GENERATED)
└── portfolio_package.json (UPDATED SCHEMA)
```

### New Files in GitHub Repository

```
wix-portfolio-assets/
├── components/ (COPIED FROM DESIGN SYSTEM)
├── projects/ (COPIED FROM EXAMPLES)
├── generated/ (AUTO-GENERATED FROM UNREAL)
│   ├── project-name-hero.html
│   ├── project-name-passport.html
│   └── deployment-manifest.json
└── index.html (MANUAL)
```

---

## Configuration Files

### 1. Deployment Configuration

**File:** `Saved/Portfolio/WebComponents/deployment_config.json`

```json
{
  "github": {
    "repository": "username/wix-portfolio-assets",
    "branch": "main",
    "auto_deploy": true,
    "commit_message_prefix": "Auto-deploy from Unreal Pipeline"
  },
  "wix": {
    "site_url": "https://username.wixsite.com/portfolio",
    "update_strategy": "iframe",
    "cache_duration": 3600
  },
  "components": {
    "source_dir": "_staging/design-system",
    "target_components": "components",
    "target_projects": "projects",
    "target_generated": "generated"
  }
}
```

### 2. Deployment Manifest (Auto-Generated)

**File:** `generated/deployment-manifest.json`

```json
{
  "version": "1.0",
  "generated_at": "2026-06-27T10:00:00Z",
  "project": {
    "name": "Project Name",
    "theme": "environment",
    "performance": "balanced"
  },
  "assets": {
    "hero": {
      "url": "https://username.github.io/wix-portfolio-assets/generated/project-hero.html",
      "theme": "dark",
      "dimensions": {"width": "100%", "height": "520px"},
      "config": {...}
    },
    "passport": {
      "url": "https://username.github.io/wix-portfolio-assets/generated/project-passport.html",
      "theme": "dark",
      "dimensions": {"width": "360px", "height": "560px"},
      "config": {...}
    }
  }
}
```

---

## Execution Examples

### Example 1: Manual Pipeline Run

```bash
# In Unreal Editor
py Content/Python/generate_portfolio.py

# Output:
# WEB_COMPONENT_GENERATION ok=true theme=environment perf=balanced
# GITHUB_DEPLOY ok=true
# GENERATE_PORTFOLIO all_ok=true
```

### Example 2: Portfolio Orchestrator Integration

Add to portfolio orchestrator rotation:

```python
# In run_portfolio_orchestrator_loop_tick.py
if tick % 6 == 5:  # Every 6th tick
    step("web_components", web_components.generate)
    if should_deploy_to_github():
        step("github_deploy", github.deploy_to_github)
```

### Example 3: Theme-Specific Output

**Environment Project:**
```json
{
  "theme": "environment",
  "hero": {
    "contentTheme": "environment",
    "auroraColors": ["rgba(110,90,166,0.4)", "rgba(60,92,158,0.3)"]
  }
}
```

**Character Project:**
```json
{
  "theme": "character",
  "hero": {
    "contentTheme": "character",
    "auroraColors": ["rgba(156,148,198,0.5)", "rgba(110,90,166,0.4)"]
  }
}
```

---

## Testing and Verification

### 1. Local Testing

**Test Web Component Generation:**
```bash
cd C:\EnvironmentPortfolio\BS_GodFile
python Content/Python/web_component_generator.py
```

**Verify Output:**
- Check `Saved/Portfolio/WebComponents/` for config files
- Validate JSON structure
- Test theme detection logic

### 2. GitHub Testing

**Test Deployment:**
```bash
python Content/Python/github_deployer.py
```

**Verify Deployment:**
- Check GitHub repository for new files
- Verify GitHub Pages is updated
- Test URLs directly in browser

### 3. Wix Testing

**Test Iframe Loading:**
1. Add iframe to Wix site
2. Test with static GitHub Pages URL
3. Test dynamic loading script
4. Verify fallback mechanisms
5. Test on mobile devices

---

## Troubleshooting Guide

### Problem: Web Components Not Generated

**Check:**
1. `portfolio_package.json` exists and is valid
2. `web_component_generator.py` is in correct location
3. Python dependencies are available
4. Unreal Python environment is working

**Solution:**
- Run `generate_portfolio.py` first to create package
- Check Python script permissions
- Verify script syntax

### Problem: GitHub Deployment Fails

**Check:**
1. Git is installed and accessible
2. SSH key or PAT is configured
3. Repository URL is correct
4. Internet connection is available

**Solution:**
- Test git clone manually
- Verify GitHub authentication
- Check repository permissions

### Problem: Wix Iframe Not Loading

**Check:**
1. GitHub Pages URL is correct
2. GitHub Pages is deployed
3. Iframe code is correct
4. Browser console for errors

**Solution:**
- Test URL directly in browser
- Check GitHub Pages deployment status
- Verify iframe dimensions
- Test with static URL first

### Problem: Components Not Animating

**Check:**
1. All component files are uploaded
2. File paths in HTML are correct
3. JavaScript is enabled
4. No script errors in console

**Solution:**
- Verify component files exist in GitHub repo
- Check file paths in generated HTML
- Test components directly from GitHub Pages
- Check browser console for errors

---

## Performance Optimization

### 1. Unreal Pipeline Optimization

**Reduce Generation Time:**
- Cache material previews
- Skip unchanged assets
- Parallelize independent operations

**Optimize File Sizes:**
- Compress render outputs
- Optimize texture resolutions
- Clean up temporary files

### 2. GitHub Optimization

**Reduce Deployment Time:**
- Use shallow clones
- Only deploy changed files
- Implement delta updates

**Optimize Repository:**
- Use .gitignore for unnecessary files
- Implement LFS for large assets
- Clean up old branches

### 3. Wix Optimization

**Reduce Load Time:**
- Implement lazy loading
- Use CDN for GitHub Pages
- Cache deployment manifest locally
- Preload critical assets

**Optimize Iframe Performance:**
- Use appropriate sizing
- Implement responsive loading
- Optimize component configuration
- Monitor load times

---

## Security and Maintenance

### Security Best Practices

1. **Never commit sensitive data** - API keys, tokens, credentials
2. **Use environment variables** - For configuration secrets
3. **Implement access controls** - Limit GitHub repository access
4. **Use HTTPS** - For all external connections
5. **Regular updates** - Keep dependencies updated

### Maintenance Schedule

**Weekly:**
- Check GitHub repository for updates
- Monitor deployment manifest versions
- Review performance metrics

**Monthly:**
- Update modular components if needed
- Review and optimize configurations
- Check for security vulnerabilities

**Quarterly:**
- Review entire pipeline performance
- Update documentation
- Plan feature enhancements

---

## Monitoring and Analytics

### Key Metrics to Track

1. **Pipeline Performance**
   - Generation time
   - Deployment success rate
   - Error frequency

2. **GitHub Performance**
   - Deployment frequency
   - Repository size
   - Traffic statistics

3. **Wix Performance**
   - Component load time
   - Error rate
   - User engagement

### Implementation

```html
<script>
// Track component load time
const startTime = performance.now();
fetch('https://username.github.io/wix-portfolio-assets/generated/deployment-manifest.json')
  .then(response => response.json())
  .then(manifest => {
    const loadTime = performance.now() - startTime;
    
    // Send to analytics
    if (typeof gtag !== 'undefined') {
      gtag('event', 'component_load', {
        'load_time': loadTime,
        'theme': manifest.project.theme
      });
    }
  });
</script>
```

---

## Future Enhancements

### Potential Additions

1. **TouchDesigner Real-Time Layer** (In Progress — `feature/touchdesigner-mcp-integration`)
   - Interactive portfolio viewer with live parameter morphing
   - Audio-reactive materials driven by Melusina VoiceSynth
   - Unified MCP orchestration (Embody + Monolith + Blender MCP)
   - See `Docs/TOUCHDESIGNER_MCP_INTEGRATION_PLAN.md`

2. **Real-time Preview**
   - Live preview in Unreal editor
   - Real-time component updates
   - Interactive theme selection

3. **Advanced Customization**
   - Custom theme editor
   - Parameter tuning interface
   - Visual configuration builder

4. **Multi-Site Deployment**
   - Support multiple Wix sites
   - Different configurations per site
   - Centralized management

5. **Analytics Dashboard**
   - Pipeline performance dashboard
   - Component usage statistics
   - User engagement metrics

---

## Support and Resources

### Documentation

- `PORTFOLIO_PIPELINE_UPDATED.md` - Enhanced pipeline specification
- `GITHUB_SETUP_GUIDE.md` - GitHub repository setup
- `WIX_IFRAME_DEPLOYMENT_STRATEGY.md` - Iframe integration details
- `MODULAR-SYSTEM-GUIDE.md` - Component usage guide
- `Docs/TOUCHDESIGNER_MCP_INTEGRATION_PLAN.md` - TouchDesigner + MCP integration architecture

### Troubleshooting

1. Check this workflow document first
2. Review individual component documentation
3. Test each phase independently
4. Check browser console for errors
5. Verify GitHub Pages deployment status

### Getting Help

For issues with:
- **Unreal Pipeline**: Check pipeline documentation
- **GitHub**: Refer to GitHub documentation
- **Wix**: Check Wix support center
- **Components**: Refer to modular system guide

---

## Success Criteria

- [x] Unreal pipeline generates web component configurations
- [x] Components are automatically themed based on content
- [x] GitHub deployment is automated and reliable
- [x] Wix iframe integration works seamlessly
- [x] Performance is optimized for web delivery
- [x] Fallback mechanisms exist for all scenarios
- [x] Documentation is complete and accurate
- [x] End-to-end workflow is tested and verified

---

## Conclusion

This integration workflow provides a complete, automated pipeline from Unreal Engine to your Wix website. The system maintains all existing functionality while adding powerful new web deployment capabilities through the modular component system and GitHub Pages hosting.

The workflow is designed to be:
- **Automated** - Minimal manual intervention required
- **Reliable** - Fallback mechanisms at every stage
- **Performant** - Optimized for web delivery
- **Maintainable** - Clear documentation and structure
- **Scalable** - Easy to extend and enhance

By following this workflow, you can focus on creating content in Unreal while the system handles deployment to your website automatically.