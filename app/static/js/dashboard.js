async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Request failed: ${url}`);
  }
  return await res.json();
}

function formatMoney(value) {
  return Number(value || 0).toFixed(2);
}

const charts = {};

function currentFilters() {
  return {
    start_time: document.getElementById("start-time").value || "",
    end_time: document.getElementById("end-time").value || "",
    region: document.getElementById("region").value || "",
    category: document.getElementById("category").value || "",
    campaign_id: document.getElementById("campaign").value || "",
    granularity: document.getElementById("granularity").value || "day",
  };
}

function buildQuery(params) {
  const p = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== "" && v !== null && v !== undefined) {
      p.append(k, v);
    }
  });
  return p.toString();
}

function setAlerts(alerts) {
  const node = document.getElementById("alerts");
  if (!alerts || alerts.length === 0) {
    node.innerText = "当前无异常预警。";
    return;
  }
  node.innerText = alerts.map((x) => `预警：${x.message}`).join(" | ");
}

function initChart(id) {
  if (!charts[id]) {
    charts[id] = echarts.init(document.getElementById(id));
  }
  return charts[id];
}

async function loadDimensions() {
  const payload = await fetchJson("/api/dashboard/dimensions");
  const { regions, categories, campaigns } = payload.data;
  const region = document.getElementById("region");
  const category = document.getElementById("category");
  const campaign = document.getElementById("campaign");
  regions.forEach((x) => region.insertAdjacentHTML("beforeend", `<option value="${x}">${x}</option>`));
  categories.forEach((x) => category.insertAdjacentHTML("beforeend", `<option value="${x}">${x}</option>`));
  campaigns.forEach((x) =>
    campaign.insertAdjacentHTML("beforeend", `<option value="${x.id}">${x.name}</option>`)
  );
}

async function loadOverview(filters) {
  const qs = buildQuery(filters);
  const payload = await fetchJson(`/api/dashboard/overview?${qs}`);
  const metrics = payload.data.metrics;
  document.getElementById("gmv").innerText = `¥${formatMoney(metrics.gmv)}`;
  document.getElementById("order-count").innerText = metrics.order_count;
  document.getElementById("conversion").innerText = `${metrics.pay_conversion_rate}%`;
  document.getElementById("aov").innerText = `¥${formatMoney(metrics.avg_order_value)}`;
  setAlerts(payload.data.alerts || []);
}

async function loadGmvTrend(filters) {
  const qs = buildQuery(filters);
  const payload = await fetchJson(`/api/dashboard/trend?${qs}`);
  const list = payload.data || [];
  const chart = initChart("gmv-trend");
  chart.setOption({
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: list.map((x) => x.bucket) },
    yAxis: { type: "value" },
    series: [
      {
        name: "GMV",
        type: "line",
        smooth: true,
        data: list.map((x) => Number(x.gmv || 0).toFixed(2)),
      },
    ],
  });
}

async function loadUserSegments(filters) {
  const qs = buildQuery(filters);
  const payload = await fetchJson(`/api/users/segments?${qs}`);
  const dist = payload.data.distribution || {};
  const chart = initChart("segment-pie");
  chart.setOption({
    tooltip: { trigger: "item" },
    legend: { top: "bottom" },
    series: [
      {
        type: "pie",
        radius: "65%",
        data: Object.keys(dist).map((k) => ({ name: k, value: dist[k] })),
      },
    ],
  });
}

async function loadDrilldown(filters) {
  const qs = buildQuery(filters);
  const payload = await fetchJson(`/api/dashboard/drilldown?${qs}`);
  const data = payload.data;

  const regionChart = initChart("region-bar");
  regionChart.setOption({
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: data.by_region.map((x) => x.region) },
    yAxis: { type: "value" },
    series: [{ type: "bar", data: data.by_region.map((x) => Number(x.gmv).toFixed(2)) }],
  });

  const categoryChart = initChart("category-bar");
  categoryChart.setOption({
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: data.by_category.map((x) => x.category) },
    yAxis: { type: "value" },
    series: [{ type: "bar", data: data.by_category.map((x) => Number(x.gmv).toFixed(2)) }],
  });
}

async function loadMarketingTable(filters) {
  const qs = buildQuery(filters);
  const payload = await fetchJson(`/api/marketing/effectiveness?${qs}`);
  const list = payload.data.campaigns || [];
  const tbody = document.querySelector("#campaign-table tbody");
  tbody.innerHTML = "";
  list.forEach((x) => {
    tbody.insertAdjacentHTML(
      "beforeend",
      `<tr>
        <td>${x.campaign_name}</td>
        <td>${x.campaign_type}</td>
        <td>${x.order_count}</td>
        <td>¥${formatMoney(x.gmv)}</td>
        <td>${x.coupon_usage_rate}%</td>
        <td>${x.roi}</td>
      </tr>`
    );
  });
}

async function refreshAll() {
  const filters = currentFilters();
  await Promise.all([
    loadOverview(filters),
    loadGmvTrend(filters),
    loadUserSegments(filters),
    loadDrilldown(filters),
    loadMarketingTable(filters),
  ]);
}

async function boot() {
  try {
    await loadDimensions();
    await refreshAll();
    document.getElementById("apply-btn").addEventListener("click", refreshAll);
  } catch (e) {
    console.error(e);
    alert("加载看板数据失败，请检查后端服务和数据库连接。");
  }
}

boot();
