<<<<<<< HEAD
document.addEventListener('DOMContentLoaded', async () => {
  const toggleSwitch = document.getElementById('toggleSwitch');
  const statusText = document.getElementById('statusText');
  const filterInput = document.getElementById('filterInput');
  const addFilterBtn = document.getElementById('addFilter');
  const filterList = document.getElementById('filterList');

  // 获取当前状态
  const response = await chrome.runtime.sendMessage({ action: "getState" });
  toggleSwitch.checked = response.isEnabled;
  updateStatus(response.isEnabled);

  // 加载现有过滤规则
  loadFilters();

  // 监听开关变化
  toggleSwitch.addEventListener('change', async (e) => {
    const isEnabled = e.target.checked;
    await chrome.runtime.sendMessage({ 
      action: "setState", 
      isEnabled 
    });
    updateStatus(isEnabled);
  });

  // 添加过滤规则
  addFilterBtn.addEventListener('click', async () => {
    const filter = filterInput.value.trim();
    if (filter) {
      const response = await chrome.runtime.sendMessage({
        action: "addFilter",
        filter: filter
      });
      if (response.success) {
        filterInput.value = '';
        updateFilterList(response.filters);
      }
    }
  });

  // 按Enter键添加过滤规则
  filterInput.addEventListener('keypress', async (e) => {
    if (e.key === 'Enter') {
      const filter = filterInput.value.trim();
      if (filter) {
        const response = await chrome.runtime.sendMessage({
          action: "addFilter",
          filter: filter
        });
        if (response.success) {
          filterInput.value = '';
          updateFilterList(response.filters);
        }
      }
    }
  });

  // 加载过滤规则列表
  async function loadFilters() {
    const response = await chrome.runtime.sendMessage({ action: "getFilterPool" });
    updateFilterList(response.filters);
  }

  // 更新过滤规则列表显示
  function updateFilterList(filters) {
    filterList.innerHTML = '';
    filters.forEach(filter => {
      const filterItem = document.createElement('div');
      filterItem.className = 'filter-item';
      filterItem.innerHTML = `
        <span>${filter}</span>
        <button class="filter-remove" data-filter="${filter}">×</button>
      `;
      filterList.appendChild(filterItem);
    });

    // 添加删除按钮的事件监听
    document.querySelectorAll('.filter-remove').forEach(button => {
      button.addEventListener('click', async () => {
        const filterToRemove = button.getAttribute('data-filter');
        const response = await chrome.runtime.sendMessage({
          action: "removeFilter",
          filter: filterToRemove
        });
        if (response.success) {
          updateFilterList(response.filters);
        }
      });
    });
  }

  function updateStatus(isEnabled) {
    statusText.textContent = isEnabled ? '已启用' : '已禁用';
    statusText.style.color = isEnabled ? '#2196F3' : '#666';
  }
});
=======
document.addEventListener('DOMContentLoaded', async () => {
  const toggleSwitch = document.getElementById('toggleSwitch');
  const statusText = document.getElementById('statusText');
  const filterInput = document.getElementById('filterInput');
  const addFilterBtn = document.getElementById('addFilter');
  const filterList = document.getElementById('filterList');

  // 获取当前状态
  const response = await chrome.runtime.sendMessage({ action: "getState" });
  toggleSwitch.checked = response.isEnabled;
  updateStatus(response.isEnabled);

  // 加载现有过滤规则
  loadFilters();

  // 监听开关变化
  toggleSwitch.addEventListener('change', async (e) => {
    const isEnabled = e.target.checked;
    await chrome.runtime.sendMessage({ 
      action: "setState", 
      isEnabled 
    });
    updateStatus(isEnabled);
  });

  // 添加过滤规则
  addFilterBtn.addEventListener('click', async () => {
    const filter = filterInput.value.trim();
    if (filter) {
      const response = await chrome.runtime.sendMessage({
        action: "addFilter",
        filter: filter
      });
      if (response.success) {
        filterInput.value = '';
        updateFilterList(response.filters);
      }
    }
  });

  // 按Enter键添加过滤规则
  filterInput.addEventListener('keypress', async (e) => {
    if (e.key === 'Enter') {
      const filter = filterInput.value.trim();
      if (filter) {
        const response = await chrome.runtime.sendMessage({
          action: "addFilter",
          filter: filter
        });
        if (response.success) {
          filterInput.value = '';
          updateFilterList(response.filters);
        }
      }
    }
  });

  // 加载过滤规则列表
  async function loadFilters() {
    const response = await chrome.runtime.sendMessage({ action: "getFilterPool" });
    updateFilterList(response.filters);
  }

  // 更新过滤规则列表显示
  function updateFilterList(filters) {
    filterList.innerHTML = '';
    filters.forEach(filter => {
      const filterItem = document.createElement('div');
      filterItem.className = 'filter-item';
      filterItem.innerHTML = `
        <span>${filter}</span>
        <button class="filter-remove" data-filter="${filter}">×</button>
      `;
      filterList.appendChild(filterItem);
    });

    // 添加删除按钮的事件监听
    document.querySelectorAll('.filter-remove').forEach(button => {
      button.addEventListener('click', async () => {
        const filterToRemove = button.getAttribute('data-filter');
        const response = await chrome.runtime.sendMessage({
          action: "removeFilter",
          filter: filterToRemove
        });
        if (response.success) {
          updateFilterList(response.filters);
        }
      });
    });
  }

  function updateStatus(isEnabled) {
    statusText.textContent = isEnabled ? '已启用' : '已禁用';
    statusText.style.color = isEnabled ? '#2196F3' : '#666';
  }
});
>>>>>>> 2d5d9d9cf12d707f2c5354c07328162bc648e520
