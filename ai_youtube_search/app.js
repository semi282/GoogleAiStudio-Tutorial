/**
 * 자막뽑기 AI - Frontend Application Logic (JavaScript)
 * 
 * Engine:
 * - STT: Gemini 3.5 Transcribe
 * - Q&A: Gemini 3.8 Flash
 */

// ================= STATE MANAGEMENT =================

let currentSession = {
  id: '',
  url: '',
  title: '',
  channel: '',
  duration: 0,
  transcript: '',
  summary: '',
  costEstimate: null,
  isCached: false,
  chatHistory: []
};

const API_BASE = (window.location.protocol.startsWith('http') && window.location.port)
  ? ''
  : 'http://127.0.0.1:8000';

let historyList = JSON.parse(localStorage.getItem('zapok_history') || '[]');

// ================= INITIALIZATION =================

window.addEventListener('DOMContentLoaded', () => {
  loadHistoryFromServer();
  checkApiConfig();
});

// ================= UTILITY FUNCTIONS =================

function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function parseTimestampToSeconds(tsStr) {
  const parts = tsStr.split(':').map(Number);
  if (parts.length === 2) {
    return (parts[0] * 60) + parts[1];
  } else if (parts.length === 3) {
    return (parts[0] * 3600) + (parts[1] * 60) + parts[2];
  }
  return 0;
}

// ================= API CONFIG & SERVER STATUS =================

function checkApiConfig() {
  fetch(`${API_BASE}/api/config`)
    .then(r => r.json())
    .then(d => {
      const badge = document.getElementById('apiKeyBadge');
      const notice = document.getElementById('modalEnvKeyNotice');
      if (d.has_env_key) {
        if (badge) badge.textContent = "API 연동됨";
        if (notice) notice.textContent = "✔ 서버 환경변수(GEMINI_API_KEY)가 정상 감지되었습니다.";
      } else {
        if (badge) badge.textContent = "API 키 입력";
        if (notice) {
          notice.textContent = "⚠️ 환경변수 없음: API 키를 입력해 주세요.";
          notice.className = "text-[11px] text-amber-400 mt-1";
        }
      }
    })
    .catch(err => {
      console.warn('Config fetch failed:', err);
      const badge = document.getElementById('apiKeyBadge');
      if (badge) badge.textContent = "서버 연결 확인";
    });
}

// ================= DRAWER & TAB NAVIGATION =================

function toggleLeftDrawer() {
  const drawer = document.getElementById('leftDrawer');
  if (!drawer) return;
  if (drawer.classList.contains('w-72')) {
    drawer.classList.remove('w-72');
    drawer.classList.add('w-0', '-translate-x-full');
  } else {
    drawer.classList.remove('w-0', '-translate-x-full');
    drawer.classList.add('w-72');
  }
}

function toggleRightDrawer() {
  const drawer = document.getElementById('rightDrawer');
  if (!drawer) return;
  if (drawer.classList.contains('w-96')) {
    drawer.classList.remove('w-96');
    drawer.classList.add('w-0', 'translate-x-full');
  } else {
    drawer.classList.remove('w-0', 'translate-x-full');
    drawer.classList.add('w-96');
  }
}

function openRightDrawer() {
  const drawer = document.getElementById('rightDrawer');
  if (!drawer) return;
  drawer.classList.remove('w-0', 'translate-x-full');
  drawer.classList.add('w-96');
}

function switchRightTab(tab) {
  const tabs = ['script', 'chat', 'summary'];
  tabs.forEach(t => {
    const capitalized = t.charAt(0).toUpperCase() + t.slice(1);
    const btn = document.getElementById(`tabBtn${capitalized}`);
    const content = document.getElementById(`tabContent${capitalized}`);
    if (!btn || !content) return;

    if (t === tab) {
      btn.className = "px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 bg-brand-hover text-white";
      content.classList.remove('hidden');
    } else {
      btn.className = "px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 text-brand-muted hover:text-white";
      content.classList.add('hidden');
    }
  });
}

function openRightTab(tab) {
  openRightDrawer();
  switchRightTab(tab);
}

// ================= YOUTUBE PLAYER & TIMESTAMPS =================

function loadYouTubeVideo(videoId, startSeconds = 0) {
  const placeholder = document.getElementById('videoPlaceholder');
  const iframe = document.getElementById('videoIframe');
  if (!placeholder || !iframe) return;

  placeholder.classList.add('hidden');
  iframe.classList.remove('hidden');

  const startParam = startSeconds > 0 ? `&start=${startSeconds}` : '';
  iframe.src = `https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0${startParam}`;
}

function seekToTime(seconds) {
  if (!currentSession.id) return;
  loadYouTubeVideo(currentSession.id, seconds);
}

// ================= STT TRANSCRIBE SEARCH (CSV CACHE FIRST) =================

async function startDirectSearch() {
  const urlInput = document.getElementById('youtubeUrl');
  const url = urlInput ? urlInput.value.trim() : '';
  if (!url) {
    alert('유튜브 영상 URL을 입력해 주세요.');
    return;
  }

  const overlay = document.getElementById('loadingOverlay');
  const statusText = document.getElementById('loadingStatusText');
  if (overlay) overlay.classList.remove('hidden');
  if (statusText) statusText.textContent = "저장된 캐시 확인 및 자막 추출 준비 중...";

  const apiKey = localStorage.getItem('zapok_api_key') || '';

  try {
    const res = await fetch(`${API_BASE}/api/transcribe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: url,
        api_key: apiKey
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || '자막 추출 실패');

    currentSession = {
      id: data.id,
      url: url,
      title: data.title,
      channel: data.channel,
      duration: data.duration,
      thumbnail: data.thumbnail,
      transcript: data.transcript,
      summary: data.summary,
      costEstimate: data.cost_estimate,
      isCached: data.is_cached || false,
      chatHistory: []
    };

    renderSession(currentSession);
    addToHistory(currentSession);
    loadHistoryFromServer();
    openRightDrawer();
    switchRightTab('script');

  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      alert('서버 연결 실패: 백엔드 서버(http://127.0.0.1:8000)가 켜져 있는지 확인해 주세요.');
    } else {
      alert('오류 발생: ' + err.message);
    }
  } finally {
    if (overlay) overlay.classList.add('hidden');
  }
}

function renderSession(s) {
  // 1. Load YouTube Video Embed
  if (s.id) {
    loadYouTubeVideo(s.id, 0);
  }

  // 2. Metadata
  const titleEl = document.getElementById('videoTitleText');
  const channelEl = document.getElementById('channelNameText');
  const avatarEl = document.getElementById('channelAvatarText');
  const metaEl = document.getElementById('videoMetaText');

  if (titleEl) titleEl.textContent = s.title || '영상 제목';
  if (channelEl) channelEl.textContent = s.channel || '채널';
  if (avatarEl) avatarEl.textContent = s.channel ? s.channel.charAt(0).toUpperCase() : 'YT';
  if (metaEl) metaEl.textContent = `재생시간: ${s.duration}초`;

  // 3. Cost Badge Display & Cache Notice
  const costBadge = document.getElementById('costInfoBadge');
  const costInfoText = document.getElementById('costInfoText');
  if (costBadge && costInfoText) {
    if (s.costEstimate) {
      costBadge.classList.remove('hidden');
      costBadge.classList.add('flex');
      const costText = s.isCached
        ? `⚡ 캐시 데이터 (API 0원)`
        : `예상 요금: ${s.costEstimate.total_cost_krw_formatted} (${s.costEstimate.total_cost_usd_formatted})`;
      costInfoText.textContent = costText;
    } else {
      costBadge.classList.remove('flex');
      costBadge.classList.add('hidden');
    }
  }

  // 4. Transcript View with Clickable Timestamps
  const tView = document.getElementById('transcriptView');
  if (tView) {
    tView.innerHTML = '';
    if (s.transcript) {
      const lines = s.transcript.split('\n');
      lines.forEach(line => {
        if (!line.trim()) return;
        const p = document.createElement('div');
        p.className = "py-1.5 px-2 rounded hover:bg-brand-hover/60 transition leading-relaxed text-xs flex items-start group";

        const tsMatch = line.match(/^\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.*)$/);
        if (tsMatch) {
          const timeStr = tsMatch[1];
          const content = tsMatch[2];
          const totalSec = parseTimestampToSeconds(timeStr);
          p.innerHTML = `
            <button onclick="seekToTime(${totalSec})" 
                    class="flex-shrink-0 inline-flex items-center gap-1 bg-brand-purple/25 hover:bg-brand-purple text-brand-purple hover:text-white px-2 py-0.5 rounded text-[11px] font-mono font-bold transition mr-1.5 shadow-sm active:scale-95 cursor-pointer select-none"
                    title="${timeStr} 구간 바로 듣기">
              <i class="fa-solid fa-play text-[8px]"></i> ${timeStr}
            </button>
            <a href="https://www.youtube.com/watch?v=${s.id}&t=${totalSec}s" target="_blank" rel="noopener noreferrer"
               class="flex-shrink-0 text-[10px] text-brand-muted/70 hover:text-brand-red mr-2 mt-0.5 transition" title="유튜브 웹에서 이 구간 열기">
              <i class="fa-solid fa-arrow-up-right-from-square"></i>
            </a>
            <span class="text-brand-text flex-1 select-text">${escapeHtml(content)}</span>
          `;
        } else {
          const formattedLine = line.replace(/\[(\d{1,2}:\d{2}(?::\d{2})?)\]/g, (match, p1) => {
            const sec = parseTimestampToSeconds(p1);
            return `<button onclick="seekToTime(${sec})" class="inline-flex items-center gap-1 bg-brand-purple/25 hover:bg-brand-purple text-brand-purple hover:text-white px-1.5 py-0.5 rounded text-[10px] font-mono font-bold transition mx-1 cursor-pointer select-none">▶ ${p1}</button>`;
          });
          p.innerHTML = `<span class="text-brand-text flex-1 select-text">${formattedLine}</span>`;
        }
        tView.appendChild(p);
      });
    } else {
      tView.innerHTML = '<p class="text-brand-muted text-center py-10">대본이 비어있습니다.</p>';
    }
  }

  // 5. Summary View
  const sumEl = document.getElementById('summaryView');
  if (sumEl) sumEl.textContent = s.summary || "요약 내용이 없습니다.";

  renderChat();
}

// ================= GEMINI 3.8 FLASH Q&A CHAT =================

async function sendChatMessage() {
  const input = document.getElementById('chatInput');
  const question = input ? input.value.trim() : '';
  if (!question) return;

  if (!currentSession.transcript) {
    alert('먼저 자막을 추출해 주세요.');
    return;
  }

  currentSession.chatHistory.push({ role: 'user', text: question });
  if (input) input.value = '';
  renderChat();

  const chatBox = document.getElementById('chatMessages');
  if (chatBox) {
    const botMsgDiv = document.createElement('div');
    botMsgDiv.className = "bg-brand-card border border-brand-border/50 rounded-xl p-3 text-brand-muted animate-pulse";
    botMsgDiv.textContent = "Gemini 3.8 Flash가 영상 대본을 분석 중입니다...";
    chatBox.appendChild(botMsgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  try {
    const apiKey = localStorage.getItem('zapok_api_key') || '';
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: question,
        transcript: currentSession.transcript,
        api_key: apiKey
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || '답변 생성 실패');

    currentSession.chatHistory.push({ role: 'assistant', text: data.answer });
  } catch (e) {
    currentSession.chatHistory.push({ role: 'assistant', text: '오류가 발생했습니다: ' + e.message });
  } finally {
    renderChat();
  }
}

function renderChat() {
  const box = document.getElementById('chatMessages');
  if (!box) return;
  box.innerHTML = '';
  
  if (currentSession.chatHistory.length === 0) {
    box.innerHTML = `
      <div class="bg-brand-card border border-brand-border/50 rounded-xl p-3 text-brand-muted">
        👋 추출된 자막을 바탕으로 궁금한 점을 질문해 보세요.<br><br>
        • "이 영상의 가장 핵심적인 내용은 뭐야?"<br>
        • "주요 발화자와 대사 내용을 정리해줘"<br>
        • "결론이나 요점을 3줄로 알려줘"
      </div>
    `;
    return;
  }

  currentSession.chatHistory.forEach(msg => {
    const el = document.createElement('div');
    if (msg.role === 'user') {
      el.className = "bg-brand-purple/20 border border-brand-purple/30 text-white rounded-xl p-3 ml-4";
      el.innerHTML = `<span class="font-bold text-brand-purple block mb-1">나의 질문:</span>${escapeHtml(msg.text)}`;
    } else {
      el.className = "bg-brand-card border border-brand-border/60 text-brand-text rounded-xl p-3 mr-2 leading-relaxed whitespace-pre-line";
      el.innerHTML = `<span class="font-bold text-emerald-400 flex items-center gap-1 mb-1"><i class="fa-solid fa-wand-magic-sparkles text-xs"></i> AI 답변 (Gemini 3.8 Flash):</span>${escapeHtml(msg.text)}`;
    }
    box.appendChild(el);
  });
  box.scrollTop = box.scrollHeight;
}

// ================= CSV HISTORY & STORAGE =================

async function loadHistoryFromServer() {
  try {
    const res = await fetch(`${API_BASE}/api/history`);
    if (res.ok) {
      const list = await res.json();
      if (Array.isArray(list) && list.length > 0) {
        historyList = list;
        localStorage.setItem('zapok_history', JSON.stringify(historyList));
        renderHistory();
        return;
      }
    }
  } catch (e) {
    console.warn('Server history fetch error:', e);
  }
  renderHistory();
}

function addToHistory(session) {
  historyList = historyList.filter(h => h.id !== session.id);
  historyList.unshift(session);
  if (historyList.length > 30) historyList.pop();
  localStorage.setItem('zapok_history', JSON.stringify(historyList));
  renderHistory();
}

function renderHistory() {
  const listEl = document.getElementById('historyList');
  if (!listEl) return;
  listEl.innerHTML = '';
  if (historyList.length === 0) {
    listEl.innerHTML = '<div class="p-6 text-center text-xs text-brand-muted">저장된 영상 기록이 없습니다.<br>상단에 링크를 입력해 보세요.</div>';
    return;
  }

  historyList.forEach(item => {
    const div = document.createElement('div');
    div.className = "p-2.5 rounded-xl hover:bg-brand-hover cursor-pointer transition flex items-center gap-2 group text-xs";
    div.onclick = () => {
      currentSession = {
        id: item.id,
        url: item.url,
        title: item.title,
        channel: item.channel,
        duration: item.duration,
        thumbnail: item.thumbnail || (item.id ? `https://img.youtube.com/vi/${item.id}/hqdefault.jpg` : ''),
        transcript: item.transcript,
        summary: item.summary,
        costEstimate: null,
        isCached: true,
        chatHistory: []
      };
      renderSession(currentSession);
      openRightDrawer();
    };

    const thumb = item.id 
      ? `<img src="https://img.youtube.com/vi/${item.id}/hqdefault.jpg" class="w-full h-full object-cover">`
      : `<i class="fa-brands fa-youtube text-brand-red"></i>`;

    div.innerHTML = `
      <div class="w-12 h-8 rounded bg-black flex-shrink-0 overflow-hidden flex items-center justify-center border border-brand-border/40">
        ${thumb}
      </div>
      <div class="flex-1 min-w-0">
        <p class="font-semibold text-white truncate">${escapeHtml(item.title) || '영상'}</p>
        <p class="text-[10px] text-brand-muted truncate">${escapeHtml(item.channel) || '채널'}</p>
      </div>
    `;
    listEl.appendChild(div);
  });
}

function clearHistory() {
  if (confirm('모든 기록을 삭제하시겠습니까?')) {
    historyList = [];
    localStorage.removeItem('zapok_history');
    renderHistory();
  }
}

function newSession() {
  const urlInput = document.getElementById('youtubeUrl');
  if (urlInput) urlInput.value = '';

  const iframe = document.getElementById('videoIframe');
  if (iframe) {
    iframe.src = '';
    iframe.classList.add('hidden');
  }

  const placeholder = document.getElementById('videoPlaceholder');
  if (placeholder) placeholder.classList.remove('hidden');

  const titleEl = document.getElementById('videoTitleText');
  if (titleEl) titleEl.textContent = '영상 제목이 여기에 표시됩니다.';

  const channelEl = document.getElementById('channelNameText');
  if (channelEl) channelEl.textContent = '채널명';

  const metaEl = document.getElementById('videoMetaText');
  if (metaEl) metaEl.textContent = '재생시간: -';

  const costBadge = document.getElementById('costInfoBadge');
  if (costBadge) costBadge.classList.add('hidden');

  const tView = document.getElementById('transcriptView');
  if (tView) tView.innerHTML = '<p class="text-brand-muted text-center py-10">상단에 유튜브 링크를 입력하면 자막을 추출합니다.</p>';

  const sumEl = document.getElementById('summaryView');
  if (sumEl) sumEl.textContent = '자막 추출이 완료되면 핵심 요약이 이곳에 표시됩니다.';

  currentSession = { id: '', url: '', title: '', channel: '', duration: 0, transcript: '', summary: '', costEstimate: null, isCached: false, chatHistory: [] };
  renderChat();
}

function copyTranscript() {
  if (!currentSession.transcript) return;
  navigator.clipboard.writeText(currentSession.transcript).then(() => {
    alert('자막 스크립트가 복사되었습니다.');
  });
}

function downloadTranscript() {
  if (!currentSession.transcript) return;
  const blob = new Blob([currentSession.transcript], { type: 'text/plain;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${(currentSession.title || '자막').replace(/[\/\\?%*:|"<>]/g, '_')}_transcript.txt`;
  a.click();
}

function openSettingsModal() {
  const modalInput = document.getElementById('modalApiKey');
  if (modalInput) modalInput.value = localStorage.getItem('zapok_api_key') || '';
  const modal = document.getElementById('settingsModal');
  if (modal) modal.classList.remove('hidden');
}

function closeSettingsModal() {
  const modal = document.getElementById('settingsModal');
  if (modal) modal.classList.add('hidden');
}

function saveSettings() {
  const modalInput = document.getElementById('modalApiKey');
  const key = modalInput ? modalInput.value.trim() : '';
  localStorage.setItem('zapok_api_key', key);
  closeSettingsModal();
  checkApiConfig();
}
