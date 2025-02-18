<<<<<<< HEAD
// 下载拦截器的状态
let isEnabled = true;

// 存储页面下载信息的Map
let pageDownloads = new Map();

// 存储被拦截的批量下载列表
let batchDownloads = [];

// 存储最近的下载请求
let recentDownloads = [];
const BATCH_THRESHOLD = 4;  // 批量下载阈值
const TIME_WINDOW = 2500;   // 时间窗口（2.5秒）

// 添加过滤池
let filterPool = new Set([]);

// 定义允许的文件后缀
const ALLOWED_EXTENSIONS = [
    // 可执行文件
    '.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm', '.appimage',
    // 压缩文件
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso',
    // 文档文件
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    // 媒体文件
    '.mp3', '.mp4', '.avi', '.mkv', '.flv', '.mov', '.wmv',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
    // 其他常见格式
    '.apk', '.ipa'
];

// 检查URL是否包含允许的文件后缀
function hasAllowedExtension(url) {
    try {
        // 移除URL参数
        const urlWithoutParams = url.split('?')[0];
        // 转换为小写进行比较
        const lowercaseUrl = urlWithoutParams.toLowerCase();
        // 检查是否包含允许的后缀
        return ALLOWED_EXTENSIONS.some(ext => lowercaseUrl.endsWith(ext));
    } catch (error) {
        console.error('检查文件后缀时出错:', error);
        return false;
    }
}

// 清理过期的下载记录
function cleanupOldDownloads() {
    const currentTime = Date.now();
    recentDownloads = recentDownloads.filter(download => 
        currentTime - download.timestamp < TIME_WINDOW
    );
}

// 检查是否为批量下载
function isBatchDownload() {
    cleanupOldDownloads();
    return recentDownloads.length >= BATCH_THRESHOLD;
}

// 检查URL是否在过滤池中
function isInFilterPool(url) {
    try {
        const lowercaseUrl = url.toLowerCase();
        return Array.from(filterPool).some(keyword => lowercaseUrl.includes(keyword));
    } catch (error) {
        console.error('检查过滤池时出错:', error);
        return false;
    }
}

// 监听标签页关闭事件
chrome.tabs.onRemoved.addListener((tabId) => {
    // 清理该标签页的下载记录
    pageDownloads.delete(tabId);
});

// 监听下载事件
chrome.downloads.onCreated.addListener(async (downloadItem) => {
    if (!isEnabled) return;

    try {
        // 检查是否由用户操作触发的下载
        if (!downloadItem.byExtensionId && !downloadItem.byExtensionName) {
            // 检查是否在过滤池中
            if (isInFilterPool(downloadItem.url)) {
                console.log('URL在过滤池中，忽略下载:', downloadItem.url);
                return;
            }

            // 检查文件后缀
            if (!hasAllowedExtension(downloadItem.url)) {
                console.log('不支持的文件类型，忽略下载:', downloadItem.url);
                return;
            }

            // 获取当前时间
            const currentTime = Date.now();
            
            // 记录本次下载
            recentDownloads.push({
                url: downloadItem.url,
                timestamp: currentTime
            });

            // 检查是否为批量下载
            if (isBatchDownload()) {
                console.log('检测到批量下载，暂停拦截:', {
                    recentCount: recentDownloads.length,
                    timeWindow: TIME_WINDOW
                });
                
                // 取消当前下载但不发送到服务器
                try {
                    await chrome.downloads.cancel(downloadItem.id);
                    console.log('已取消浏览器下载（批量下载模式）:', downloadItem.url);
                } catch (error) {
                    console.error('取消下载失败:', error);
                }
                return;
            }

            // 记录下载唤醒时间
            console.log('下载被唤醒:', {
                url: downloadItem.url,
                time: currentTime,
                downloadItem: {
                    byExtensionId: downloadItem.byExtensionId,
                    byExtensionName: downloadItem.byExtensionName,
                    filename: downloadItem.filename,
                    state: downloadItem.state
                }
            });

            // 发送到下载服务器并取消浏览器下载
            try {
                await fetch('http://localhost:8888', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        url: downloadItem.url,
                        timestamp: currentTime 
                    })
                });
                
                // 取消浏览器的下载
                await chrome.downloads.cancel(downloadItem.id);
                console.log('已取消浏览器下载并发送至服务器:', downloadItem.url);
            } catch (error) {
                console.error('发送到下载器失败:', error);
            }
        } else {
            console.log('下载由扩展程序触发，忽略:', {
                url: downloadItem.url,
                byExtensionId: downloadItem.byExtensionId,
                byExtensionName: downloadItem.byExtensionName
            });
        }

    } catch (error) {
        console.error('处理下载时出错:', error);
    }
});

// 从存储中加载过滤池
async function loadFilterPool() {
    try {
        const result = await chrome.storage.sync.get('filterPool');
        if (result.filterPool) {
            filterPool = new Set(result.filterPool);
            console.log('已从存储加载过滤池:', Array.from(filterPool));
        }
    } catch (error) {
        console.error('加载过滤池失败:', error);
    }
}

// 保存过滤池到存储
async function saveFilterPool() {
    try {
        await chrome.storage.sync.set({
            filterPool: Array.from(filterPool)
        });
        console.log('过滤池已保存:', Array.from(filterPool));
    } catch (error) {
        console.error('保存过滤池失败:', error);
    }
}

// 在扩展启动时加载过滤池
loadFilterPool();

// 更新消息监听器
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getBatchDownloads") {
        sendResponse({ downloads: batchDownloads });
    } else if (request.action === "clearBatchDownloads") {
        batchDownloads = [];
        chrome.action.setBadgeText({ text: '' });
        sendResponse({ success: true });
    } else if (request.action === "downloadSelected") {
        sendResponse({ success: true });
    } else if (request.action === "getState") {
        sendResponse({ isEnabled });
    } else if (request.action === "setState") {
        isEnabled = request.isEnabled;
        sendResponse({ success: true });
    } else if (request.action === "getFilterPool") {
        sendResponse({ filters: Array.from(filterPool) });
    } else if (request.action === "addFilter") {
        filterPool.add(request.filter.toLowerCase());
        saveFilterPool(); // 保存更改
        sendResponse({ success: true, filters: Array.from(filterPool) });
    } else if (request.action === "removeFilter") {
        filterPool.delete(request.filter.toLowerCase());
        saveFilterPool(); // 保存更改
        sendResponse({ success: true, filters: Array.from(filterPool) });
    }
    return true;
});

// 定期检查服务器状态
async function checkServer() {
    try {
        const response = await fetch('http://localhost:8888', {
            method: 'HEAD',
            headers: {
                'Accept': 'application/json'
            }
        });
        const isOnline = response.ok;
        console.log('服务器状态:', isOnline ? '在线' : '离线');
        return isOnline;
    } catch (error) {
        console.log('服务器离线:', error.message);
        return false;
    }
}

// 每30秒检查一次服务器状态
setInterval(checkServer, 30000);
// 启动时立即检查一次
checkServer();
=======
// 下载拦截器的状态
let isEnabled = true;

// 存储页面下载信息的Map
let pageDownloads = new Map();

// 存储被拦截的批量下载列表
let batchDownloads = [];

// 存储最近的下载请求
let recentDownloads = [];
const BATCH_THRESHOLD = 4;  // 批量下载阈值
const TIME_WINDOW = 2500;   // 时间窗口（2.5秒）

// 添加过滤池
let filterPool = new Set([]);

// 定义允许的文件后缀
const ALLOWED_EXTENSIONS = [
    // 可执行文件
    '.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm', '.appimage',
    // 压缩文件
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso',
    // 文档文件
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    // 媒体文件
    '.mp3', '.mp4', '.avi', '.mkv', '.flv', '.mov', '.wmv',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
    // 其他常见格式
    '.apk', '.ipa'
];

// 检查URL是否包含允许的文件后缀
function hasAllowedExtension(url) {
    try {
        // 移除URL参数
        const urlWithoutParams = url.split('?')[0];
        // 转换为小写进行比较
        const lowercaseUrl = urlWithoutParams.toLowerCase();
        // 检查是否包含允许的后缀
        return ALLOWED_EXTENSIONS.some(ext => lowercaseUrl.endsWith(ext));
    } catch (error) {
        console.error('检查文件后缀时出错:', error);
        return false;
    }
}

// 清理过期的下载记录
function cleanupOldDownloads() {
    const currentTime = Date.now();
    recentDownloads = recentDownloads.filter(download => 
        currentTime - download.timestamp < TIME_WINDOW
    );
}

// 检查是否为批量下载
function isBatchDownload() {
    cleanupOldDownloads();
    return recentDownloads.length >= BATCH_THRESHOLD;
}

// 检查URL是否在过滤池中
function isInFilterPool(url) {
    try {
        const lowercaseUrl = url.toLowerCase();
        return Array.from(filterPool).some(keyword => lowercaseUrl.includes(keyword));
    } catch (error) {
        console.error('检查过滤池时出错:', error);
        return false;
    }
}

// 监听标签页关闭事件
chrome.tabs.onRemoved.addListener((tabId) => {
    // 清理该标签页的下载记录
    pageDownloads.delete(tabId);
});

// 监听下载事件
chrome.downloads.onCreated.addListener(async (downloadItem) => {
    if (!isEnabled) return;

    try {
        // 检查是否由用户操作触发的下载
        if (!downloadItem.byExtensionId && !downloadItem.byExtensionName) {
            // 检查是否在过滤池中
            if (isInFilterPool(downloadItem.url)) {
                console.log('URL在过滤池中，忽略下载:', downloadItem.url);
                return;
            }

            // 检查文件后缀
            if (!hasAllowedExtension(downloadItem.url)) {
                console.log('不支持的文件类型，忽略下载:', downloadItem.url);
                return;
            }

            // 获取当前时间
            const currentTime = Date.now();
            
            // 记录本次下载
            recentDownloads.push({
                url: downloadItem.url,
                timestamp: currentTime
            });

            // 检查是否为批量下载
            if (isBatchDownload()) {
                console.log('检测到批量下载，暂停拦截:', {
                    recentCount: recentDownloads.length,
                    timeWindow: TIME_WINDOW
                });
                
                // 取消当前下载但不发送到服务器
                try {
                    await chrome.downloads.cancel(downloadItem.id);
                    console.log('已取消浏览器下载（批量下载模式）:', downloadItem.url);
                } catch (error) {
                    console.error('取消下载失败:', error);
                }
                return;
            }

            // 记录下载唤醒时间
            console.log('下载被唤醒:', {
                url: downloadItem.url,
                time: currentTime,
                downloadItem: {
                    byExtensionId: downloadItem.byExtensionId,
                    byExtensionName: downloadItem.byExtensionName,
                    filename: downloadItem.filename,
                    state: downloadItem.state
                }
            });

            // 发送到下载服务器并取消浏览器下载
            try {
                await fetch('http://localhost:8888', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        url: downloadItem.url,
                        timestamp: currentTime 
                    })
                });
                
                // 取消浏览器的下载
                await chrome.downloads.cancel(downloadItem.id);
                console.log('已取消浏览器下载并发送至服务器:', downloadItem.url);
            } catch (error) {
                console.error('发送到下载器失败:', error);
            }
        } else {
            console.log('下载由扩展程序触发，忽略:', {
                url: downloadItem.url,
                byExtensionId: downloadItem.byExtensionId,
                byExtensionName: downloadItem.byExtensionName
            });
        }

    } catch (error) {
        console.error('处理下载时出错:', error);
    }
});

// 从存储中加载过滤池
async function loadFilterPool() {
    try {
        const result = await chrome.storage.sync.get('filterPool');
        if (result.filterPool) {
            filterPool = new Set(result.filterPool);
            console.log('已从存储加载过滤池:', Array.from(filterPool));
        }
    } catch (error) {
        console.error('加载过滤池失败:', error);
    }
}

// 保存过滤池到存储
async function saveFilterPool() {
    try {
        await chrome.storage.sync.set({
            filterPool: Array.from(filterPool)
        });
        console.log('过滤池已保存:', Array.from(filterPool));
    } catch (error) {
        console.error('保存过滤池失败:', error);
    }
}

// 在扩展启动时加载过滤池
loadFilterPool();

// 更新消息监听器
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getBatchDownloads") {
        sendResponse({ downloads: batchDownloads });
    } else if (request.action === "clearBatchDownloads") {
        batchDownloads = [];
        chrome.action.setBadgeText({ text: '' });
        sendResponse({ success: true });
    } else if (request.action === "downloadSelected") {
        sendResponse({ success: true });
    } else if (request.action === "getState") {
        sendResponse({ isEnabled });
    } else if (request.action === "setState") {
        isEnabled = request.isEnabled;
        sendResponse({ success: true });
    } else if (request.action === "getFilterPool") {
        sendResponse({ filters: Array.from(filterPool) });
    } else if (request.action === "addFilter") {
        filterPool.add(request.filter.toLowerCase());
        saveFilterPool(); // 保存更改
        sendResponse({ success: true, filters: Array.from(filterPool) });
    } else if (request.action === "removeFilter") {
        filterPool.delete(request.filter.toLowerCase());
        saveFilterPool(); // 保存更改
        sendResponse({ success: true, filters: Array.from(filterPool) });
    }
    return true;
});

// 定期检查服务器状态
async function checkServer() {
    try {
        const response = await fetch('http://localhost:8888', {
            method: 'HEAD',
            headers: {
                'Accept': 'application/json'
            }
        });
        const isOnline = response.ok;
        console.log('服务器状态:', isOnline ? '在线' : '离线');
        return isOnline;
    } catch (error) {
        console.log('服务器离线:', error.message);
        return false;
    }
}

// 每30秒检查一次服务器状态
setInterval(checkServer, 30000);
// 启动时立即检查一次
checkServer();
>>>>>>> 2d5d9d9cf12d707f2c5354c07328162bc648e520
