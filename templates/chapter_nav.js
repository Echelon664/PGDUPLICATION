    // ---------------------------------------------------------------------
    // Chapter browser: a sticky toolbar above chapters that open to show their
    // documents, each with its date, summary and PDF buttons.
    // Inlined into index.html by generate_preview.py (edit this file, then
    // regenerate). Uses DOCS_BY_ID, activeProgram, escapeHtml, viewDocPdf,
    // docOpenUrl, pdfViewerUrl, isSourceMissing, docDateLine and formatLongDate from the page.
    // ---------------------------------------------------------------------
    const CN_PROGRAMS = ['CalFresh', 'CalWORKs', 'Medi-Cal'];
    const CN_PROGRAM_TITLES = { 'CalFresh': 'CalFresh (SNAP)', 'CalWORKs': 'CalWORKs (TANF)', 'Medi-Cal': 'Medi-Cal (Medicaid)' };
    let cnChapters = [];

    function cnSlug(text) {
      return String(text || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    }

    function cnProgramOf(doc) {
      return (doc.programs && doc.programs[0]) || 'CalFresh';
    }

    function cnIsNotices(name) {
      return /special notices/i.test(name || '');
    }

    // "ARTICLE 04 - APPLICATION PROCESS" -> code "Article 04", name "Application process"
    function cnSplitName(name) {
      let code = '';
      let rest = name;
      const numbered = name.match(/^(\d{2}-\d{3,4})\s+(.*)$/);
      const article = name.match(/^(ARTICLE\s+\d+)\s*[-–:]*\s*(.*)$/i);
      if (numbered) { code = numbered[1]; rest = numbered[2]; }
      else if (article) { code = 'Article ' + article[1].replace(/\D+/g, ''); rest = article[2]; }
      else if (cnIsNotices(name)) { rest = 'Special notices'; }
      if (rest && rest === rest.toUpperCase() && /[A-Z]{3}/.test(rest)) {
        rest = rest.toLowerCase().replace(/(^|[\s\-/(])([a-z])/g, (m, a, b) => a + b.toUpperCase())
          .replace(/\b(And|Of|The|For|To|In|Or)\b/g, w => w.toLowerCase())
          .replace(/\b(Magi|Aptc|Ssi|Ssp|Noa|Ict)\b/g, w => w.toUpperCase());
        rest = rest.charAt(0).toUpperCase() + rest.slice(1);
      }
      return { code, name: rest || name };
    }

    function cnNoticeYear(doc) {
      const m = /(?:^|\b)(?:SN[ _-]*)?(\d{2})[-_ ](\d{2})\b/.exec((doc.section_num || '') + ' ' + (doc.title || ''));
      if (m) return 2000 + parseInt(m[1], 10);
      const d = /^(\d{4})/.exec(doc.pdf_date || doc.published_on || '');
      return d ? parseInt(d[1], 10) : 0;
    }

    function cnNoticeNumber(doc) {
      const m = /(?:SN[ _-]*)?(\d{2})[-_ ](\d{2})\b/.exec((doc.section_num || '') + ' ' + (doc.title || ''));
      return m ? parseInt(m[2], 10) : 0;
    }

    function cnBuildChapters(docs) {
      const byKey = {};
      const list = [];
      docs.forEach(doc => {
        const program = cnProgramOf(doc);
        const category = doc.category || 'General sections';
        const key = program + '|' + category;
        if (!byKey[key]) {
          const parts = cnSplitName(category);
          byKey[key] = {
            key, program, category,
            id: cnSlug(program) + '-' + cnSlug(category),
            code: parts.code, name: parts.name,
            desc: doc.category_desc || '',
            order: doc.order || 50,
            notices: cnIsNotices(category),
            docs: []
          };
          list.push(byKey[key]);
        }
        byKey[key].docs.push(doc);
      });
      list.forEach(ch => {
        if (ch.notices) {
          ch.order = 9999;
          ch.docs.sort((a, b) => (cnNoticeYear(b) - cnNoticeYear(a)) || (cnNoticeNumber(b) - cnNoticeNumber(a)));
        }
      });
      list.sort((a, b) =>
        (CN_PROGRAMS.indexOf(a.program) - CN_PROGRAMS.indexOf(b.program)) || (a.order - b.order));
      return list;
    }

    // "Includes: Household Concept, Filing an Application, and 12 more." for the chapter header.
    const CN_INCLUDES_SHOWN = 6;
    function cnIncludesText(chapter) {
      if (chapter.notices || chapter.docs.length < 2) return '';
      const names = [];
      chapter.docs.forEach(doc => {
        const name = (doc.section_title || doc.title || '')
          .replace(/^[A-Z]\.\s+/, '')
          .replace(/^(Section\s+)?\d[\w.]*\s*[-–:]?\s*/i, '')
          .trim();
        if (name && !names.includes(name)) names.push(name);
      });
      if (names.length < 2) return '';
      const shown = names.slice(0, CN_INCLUDES_SHOWN);
      const more = names.length - shown.length;
      return 'Includes: ' + shown.join(', ') + (more > 0 ? ', and ' + more + ' more.' : '.');
    }

    function cnShortDate(doc) {
      const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(doc.pdf_date || '');
      if (!m) return '';
      return new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]))
        .toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', timeZone: 'UTC' });
    }

    function cnEl(tag, className, text) {
      const node = document.createElement(tag);
      if (className) node.className = className;
      if (text !== undefined && text !== null) node.textContent = text;
      return node;
    }

    const CN_CHEVRON = '<svg class="cn-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>';

    function cnReadHash() {
      const out = {};
      window.location.hash.replace(/^#/, '').split('&').forEach(pair => {
        const i = pair.indexOf('=');
        if (i > 0) out[pair.slice(0, i)] = decodeURIComponent(pair.slice(i + 1));
      });
      return out;
    }

    function cnWriteHash(state) {
      const parts = [];
      if (state.doc) parts.push('doc=' + encodeURIComponent(state.doc));
      else if (state.ch) parts.push('ch=' + encodeURIComponent(state.ch));
      const url = window.location.pathname + window.location.search + (parts.length ? '#' + parts.join('&') : '');
      try { window.history.replaceState(window.history.state, '', url); } catch (err) { /* file:// or sandboxed */ }
    }

    function cnBuildDetail(doc, opts) {
      const detail = cnEl('div', 'cn-detail');
      const text = cnEl('div', 'cn-detail-text');
      if (opts && opts.title) {
        // The title opens the PDF too, the same as the View PDF button.
        const title = cnEl('h6', 'cn-doc-title');
        const link = cnEl('button', 'cn-doc-link', doc.title || doc.id);
        link.type = 'button';
        link.title = isSourceMissing(doc) ? 'Open on the County site' : 'View PDF';
        link.addEventListener('click', () => viewDocPdf(doc.id));
        title.append(link);
        if (isSourceMissing(doc)) title.append(cnEl('span', 'cn-flag', 'Not bundled'));
        text.append(title);
      }
      const dateLine = docDateLine(doc);
      const posted = formatLongDate(doc.published_on || '');
      if (dateLine || posted) {
        const meta = cnEl('p', 'cn-meta');
        if (dateLine) meta.append(cnEl('strong', '', dateLine));
        if (dateLine && posted) meta.append(document.createTextNode(' · '));
        if (posted) meta.append(document.createTextNode('Posted on County site: ' + posted));
        text.append(meta);
      }
      text.append(cnEl('p', 'cn-summary', doc.summary || 'County of San Diego Health and Human Services Agency policy document.'));
      detail.append(text);

      const actions = cnEl('div', 'cn-actions');
      const missing = isSourceMissing(doc);
      const view = cnEl('button', 'cn-btn cn-btn-primary');
      view.type = 'button';
      view.append(cnEl('span', '', missing ? 'Open County site' : 'View PDF'));
      view.addEventListener('click', () => viewDocPdf(doc.id));
      actions.append(view);

      if (!missing) {
        const tab = cnEl('a', 'cn-btn cn-btn-newtab');
        tab.href = pdfViewerUrl(docOpenUrl(doc));
        tab.target = '_blank';
        tab.rel = 'noopener';
        tab.append(cnEl('span', '', 'Open in new tab'));
        actions.append(tab);
      }
      detail.append(actions);
      return detail;
    }

    function cnBuildDocBlock(doc) {
      const block = cnBuildDetail(doc, { title: true });
      block.classList.add('cn-doc');
      block.id = 'doc-' + doc.id;
      return block;
    }

    function cnFillBody(chapter, body) {
      if (body.dataset.filled) return;
      body.dataset.filled = '1';
      if (chapter.docs.length === 1) {
        // A one-document chapter opens straight to the document.
        const only = cnBuildDetail(chapter.docs[0]);
        only.classList.add('cn-detail-solo');
        body.append(only);
        return;
      }
      let lastYear = null;
      chapter.docs.forEach(doc => {
        if (chapter.notices) {
          const year = cnNoticeYear(doc);
          if (year !== lastYear) {
            lastYear = year;
            body.append(cnEl('div', 'cn-year', year ? String(year) : 'Undated'));
          }
        }
        body.append(cnBuildDocBlock(doc));
      });
    }

    function cnSetChapterOpen(chapter, open) {
      const section = document.getElementById('ch-' + chapter.id);
      if (!section) return;
      const head = section.querySelector('.cn-head');
      const body = section.querySelector('.cn-body');
      if (open) cnFillBody(chapter, body);
      body.hidden = !open;
      head.setAttribute('aria-expanded', open ? 'true' : 'false');
      section.classList.toggle('is-open', open);
    }

    function cnGoToChapter(chapterId, opts) {
      const chapter = cnChapters.find(ch => ch.id === chapterId);
      if (!chapter) return;
      cnSetChapterOpen(chapter, true);
      const section = document.getElementById('ch-' + chapter.id);
      if (!opts || opts.scroll !== false) section.scrollIntoView({ behavior: 'smooth', block: 'start' });
      if (!opts || opts.hash !== false) cnWriteHash({ ch: chapter.id });
    }

    function cnCollapseAll() {
      cnChapters.forEach(ch => cnSetChapterOpen(ch, false));
      cnWriteHash({});
    }

    function cnOpenFromHash() {
      const state = cnReadHash();
      if (state.doc && DOCS_BY_ID[state.doc]) {
        const doc = DOCS_BY_ID[state.doc];
        const chapter = cnChapters.find(ch => ch.docs.some(d => d.id === doc.id));
        if (!chapter) return false;
        cnGoToChapter(chapter.id, { scroll: false, hash: false });
        const block = document.getElementById('doc-' + doc.id);
        if (block) {
          block.classList.add('is-target');
          setTimeout(() => block.classList.remove('is-target'), 2500);
        }
        (block || document.getElementById('ch-' + chapter.id)).scrollIntoView({ block: 'start' });
        return true;
      }
      if (state.ch && cnChapters.some(ch => ch.id === state.ch)) {
        cnGoToChapter(state.ch, { hash: false });
        return true;
      }
      return false;
    }

    function renderDropdownsView(docs) {
      const meta = PROGRAM_METADATA[activeProgram];
      const heading = document.getElementById('listHeading');
      if (heading) {
        heading.textContent = (activeProgram === 'All' ? 'All programs' : meta.title) + ' policy manual (' + docs.length + ' documents)';
      }
      const container = document.getElementById('documentsList');
      if (!container) return;
      container.replaceChildren();
      container.className = 'cn-layout';

      cnChapters = cnBuildChapters(docs);
      const showPrograms = activeProgram === 'All';

      // Toolbar: jump menu and collapse all. Stays at the top while scrolling.
      const toolbar = cnEl('div', 'cn-toolbar');
      const jump = cnEl('select', 'cn-jump');
      jump.setAttribute('aria-label', 'Jump to chapter');
      jump.append(new Option('Jump to chapter…', ''));
      jump.addEventListener('change', () => { if (jump.value) cnGoToChapter(jump.value); jump.value = ''; });
      const collapse = cnEl('button', 'cn-collapse', 'Collapse all');
      collapse.type = 'button';
      collapse.addEventListener('click', cnCollapseAll);
      toolbar.append(jump, collapse);

      const main = cnEl('div', 'cn-main');

      let lastProgram = null;
      let jumpGroup = jump;
      cnChapters.forEach(chapter => {
        if (showPrograms && chapter.program !== lastProgram) {
          lastProgram = chapter.program;
          const title = CN_PROGRAM_TITLES[chapter.program] || chapter.program;
          main.append(cnEl('h4', 'cn-program-heading cn-program-title', title));
          jumpGroup = document.createElement('optgroup');
          jumpGroup.label = title;
          jump.append(jumpGroup);
        }
        const count = chapter.docs.length;
        const label = (chapter.code ? chapter.code + ' ' : '') + chapter.name;

        jumpGroup.append(new Option(label + ' (' + count + ')', chapter.id));

        const section = cnEl('section', 'cn-chapter');
        section.id = 'ch-' + chapter.id;
        section.dataset.chapter = chapter.id;
        section.dataset.program = chapter.program;
        const head = cnEl('button', 'cn-head');
        head.type = 'button';
        head.setAttribute('aria-expanded', 'false');
        head.setAttribute('aria-controls', 'cn-body-' + chapter.id);
        head.insertAdjacentHTML('beforeend', CN_CHEVRON);
        if (chapter.code) head.append(cnEl('span', 'cn-code', chapter.code));
        else if (chapter.notices) head.append(cnEl('span', 'cn-code cn-code-notices', 'Notices'));
        const text = cnEl('span', 'cn-head-text');
        let headName = chapter.name;
        if (count === 1 && !chapter.notices) {
          // "Learning Disabilities: A. Learning Disabilities" would say the same thing twice.
          const docTitle = chapter.docs[0].title || '';
          const bare = docTitle.replace(/^[A-Z]\.\s+/, '').replace(/^(Section\s+)?[\d.]+\s*[-–]?\s*/i, '');
          const a = cnSlug(bare);
          const b = cnSlug(chapter.name);
          if (a === b || b.includes(a)) headName = chapter.name;
          else if (a.includes(b)) headName = bare;
          else headName = chapter.name + ': ' + docTitle;
        }
        text.append(cnEl('span', 'cn-head-name', headName));
        if (chapter.desc) text.append(cnEl('span', 'cn-head-desc', chapter.desc));
        const includes = cnIncludesText(chapter);
        if (includes) text.append(cnEl('span', 'cn-head-includes', includes));
        head.append(text);
        const single = count === 1 ? cnShortDate(chapter.docs[0]) : '';
        head.append(cnEl('span', 'cn-count', count === 1 ? (single || '1 document') : count + ' documents'));
        head.addEventListener('click', () => {
          const open = head.getAttribute('aria-expanded') !== 'true';
          cnSetChapterOpen(chapter, open);
          cnWriteHash(open ? { ch: chapter.id } : {});
        });
        const body = cnEl('div', 'cn-body');
        body.id = 'cn-body-' + chapter.id;
        body.hidden = true;
        const headingWrap = cnEl(showPrograms ? 'h5' : 'h4', 'cn-head-wrap');
        headingWrap.append(head);
        section.append(headingWrap, body);
        main.append(section);
      });

      container.append(toolbar, main);
      cnOpenFromHash();
    }

    // Kept for older bookmarks and inline handlers.
    function expandAllChapters() { cnChapters.forEach(ch => cnSetChapterOpen(ch, true)); }
    function collapseAllChapters() { cnCollapseAll(); }

    // A shared link to a document in another program switches to that program first.
    function cnHandleDeepLink() {
      const state = cnReadHash();
      const doc = state.doc && DOCS_BY_ID[state.doc];
      if (doc && activeProgram !== 'All' && cnProgramOf(doc) !== activeProgram) {
        switchProgram(cnProgramOf(doc));
      } else {
        cnOpenFromHash();
      }
    }
    window.addEventListener('hashchange', cnHandleDeepLink);
