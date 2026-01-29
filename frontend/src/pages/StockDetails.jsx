import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, TrendingUp, TrendingDown, DollarSign, Activity, Calendar, Clock, BarChart3, AlertTriangle, RefreshCw } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const API_BASE = "http://localhost:8000";

const StockDetails = () => {
    const { symbol } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [graphData, setGraphData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [graphLoading, setGraphLoading] = useState(false);
    const [error, setError] = useState(null);
    const [financials, setFinancials] = useState([]);
    const [activePeriod, setActivePeriod] = useState("1d");

    useEffect(() => {
        const fetchDetails = async (isUpdate = false) => {
            try {
                // If it's a generic symbol like "RELIANCE", backend handles appending .NS
                const res = await axios.get(`${API_BASE}/stock/${symbol}`);
                setData(res.data);
            } catch (err) {
                console.error("Error fetching stock details:", err);
                if (!isUpdate) {
                    setError("Failed to load stock data. Please check the symbol or try again.");
                }
            } finally {
                if (!isUpdate) setLoading(false);
            }
        };

        if (symbol) {
            fetchDetails();
            // Fetch graph initially
            fetchGraphData("1d");
            // Fetch financials
            axios.get(`${API_BASE}/stock/${symbol}/financials`)
                .then(res => setFinancials(res.data))
                .catch(err => console.error("Error fetching financials:", err));

            // Poll every 5 seconds
            const intervalId = setInterval(() => {
                fetchDetails(true);
            }, 5000);

            return () => clearInterval(intervalId);
        }
    }, [symbol]);

    const fetchGraphData = async (period) => {
        setGraphLoading(true);
        setActivePeriod(period);
        try {
            const res = await axios.get(`${API_BASE}/stock/${symbol}/history?period=${period}`);
            setGraphData(res.data);
        } catch (err) {
            console.error("Error fetching history:", err);
        } finally {
            setGraphLoading(false);
        }
    };

    const formatCurrency = (val) => {
        if (typeof val !== 'number') return "-";
        return val.toLocaleString('en-IN', { style: 'currency', currency: 'INR' });
    };

    const formatNumber = (val) => {
        if (typeof val !== 'number') return "-";
        return val.toLocaleString('en-IN');
    };

    const formatIndianCompact = (num) => {
        if (!num) return "-";
        if (num >= 10000000) {
            return `₹${(num / 10000000).toLocaleString('en-IN', { maximumFractionDigits: 2 })} Cr`;
        }
        if (num >= 100000) {
            return `₹${(num / 100000).toLocaleString('en-IN', { maximumFractionDigits: 2 })} Lakh`;
        }
        return num.toLocaleString('en-IN', { style: 'currency', currency: 'INR' });
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-50 dark:bg-[#0a0c10] flex items-center justify-center text-slate-500">
                <div className="flex flex-col items-center gap-4">
                    <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
                    <p className="font-semibold animate-pulse">Loading Market Data...</p>
                </div>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="min-h-screen bg-slate-50 dark:bg-[#0a0c10] flex items-center justify-center p-6">
                <div className="bg-white dark:bg-[#13161b] p-8 rounded-2xl shadow-xl max-w-md w-full text-center border border-slate-200 dark:border-white/5">
                    <div className="w-16 h-16 bg-rose-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                        <AlertTriangle className="w-8 h-8 text-rose-500" />
                    </div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Error Loading Data</h2>
                    <p className="text-slate-500 dark:text-gray-400 mb-6">{error || "Stock not found."}</p>
                    <button
                        onClick={() => navigate('/')}
                        className="px-6 py-2 bg-slate-200 dark:bg-white/5 hover:bg-slate-300 dark:hover:bg-white/10 rounded-xl font-semibold transition-colors"
                    >
                        Back to Dashboard
                    </button>
                </div>
            </div>
        );
    }

    const isPositive = data.change >= 0;
    const ColorClass = isPositive ? 'text-emerald-500' : 'text-rose-500';
    const BgClass = isPositive ? 'bg-emerald-500/10' : 'bg-rose-500/10';
    const Icon = isPositive ? TrendingUp : TrendingDown;
    const ChartColor = isPositive ? "#10b981" : "#f43f5e";

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-[#0a0c10] text-slate-900 dark:text-white transition-colors duration-300">
            {/* Header / Nav */}
            <div className="sticky top-0 z-50 bg-white/80 dark:bg-[#0a0c10]/80 backdrop-blur-xl border-b border-slate-200 dark:border-white/10 px-6 py-4 flex items-center gap-4">
                <button
                    onClick={() => navigate(-1)}
                    className="p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-white/5 transition-colors"
                >
                    <ArrowLeft className="w-5 h-5" />
                </button>
                <div className="flex-1">
                    <h1 className="text-lg font-bold flex items-center gap-2">
                        {data.name || data.symbol}
                        <span className="text-xs font-mono bg-slate-200 dark:bg-white/10 px-2 py-0.5 rounded text-slate-500 dark:text-gray-400">{data.symbol}</span>
                    </h1>
                </div>
            </div>

            <div className="max-w-5xl mx-auto p-6 space-y-6">
                {/* Main Price Card */}
                <div className="bg-white dark:bg-[#13161b] rounded-3xl p-8 border border-slate-200 dark:border-white/5 shadow-xl relative overflow-hidden">
                    {/* Background Glow */}
                    <div className={`absolute top-0 right-0 w-[300px] h-[300px] rounded-full blur-[100px] opacity-20 pointer-events-none ${isPositive ? 'bg-emerald-500' : 'bg-rose-500'}`} />

                    <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-8">
                        <div>
                            <p className="text-sm font-bold text-slate-500 dark:text-gray-400 uppercase tracking-widest mb-1">Current Price</p>
                            <h2 className="text-5xl md:text-6xl font-black tracking-tight flex items-baseline gap-1">
                                <span className="text-lg text-slate-400 font-bold">₹</span>
                                {data.price.toLocaleString()}
                            </h2>
                        </div>

                        <div className={`px-6 py-4 rounded-2xl flex flex-col items-end ${BgClass} ${ColorClass} border border-current/10`}>
                            <div className="flex items-center gap-2 text-2xl font-bold">
                                <Icon className="w-6 h-6" />
                                {data.change > 0 ? '+' : ''}{data.change}
                            </div>
                            <div className="font-mono font-semibold opacity-90">
                                ({data.percent_change}%)
                            </div>
                        </div>
                    </div>

                    {/* Interactive Graph Section */}
                    <div className="relative z-10">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest">Price History</h3>
                            <div className="flex bg-slate-100 dark:bg-white/5 rounded-xl p-1 gap-1">
                                {['1d', '5d', '1mo', '6mo', '1y', 'max'].map((period) => (
                                    <button
                                        key={period}
                                        onClick={() => fetchGraphData(period)}
                                        className={`px-3 py-1 text-xs font-bold rounded-lg transition-all ${activePeriod === period
                                            ? 'bg-white dark:bg-gray-800 text-blue-600 shadow-sm'
                                            : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
                                            }`}
                                    >
                                        {period.toUpperCase()}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="h-[300px] w-full bg-slate-50/50 dark:bg-black/20 rounded-2xl border border-slate-200 dark:border-white/5 p-4 relative">
                            {graphLoading && (
                                <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/50 dark:bg-black/50 backdrop-blur-sm rounded-2xl">
                                    <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
                                </div>
                            )}
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={graphData}>
                                    <defs>
                                        <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor={ChartColor} stopOpacity={0.3} />
                                            <stop offset="95%" stopColor={ChartColor} stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} strokeOpacity={0.1} />
                                    <XAxis
                                        dataKey="date"
                                        hide={true}
                                    />
                                    <YAxis
                                        domain={['auto', 'auto']}
                                        hide={true}
                                    />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '12px', color: '#fff' }}
                                        itemStyle={{ color: '#fff' }}
                                        labelStyle={{ color: '#94a3b8', marginBottom: '4px', fontSize: '10px' }}
                                        formatter={(value) => [`₹${value}`, 'Price']}
                                        labelFormatter={(label) => {
                                            const d = new Date(label);
                                            if (['1d', '5d'].includes(activePeriod)) {
                                                return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                                            }
                                            return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
                                        }}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="price"
                                        stroke={ChartColor}
                                        strokeWidth={3}
                                        fillOpacity={1}
                                        fill="url(#colorPrice)"
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                            {graphData.length === 0 && !graphLoading && (
                                <div className="absolute inset-0 flex items-center justify-center text-slate-400 text-sm">
                                    No chart data available
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="mt-8 flex items-center gap-2 text-xs font-semibold text-slate-400">
                        <div className={`w-2 h-2 rounded-full ${isPositive ? 'bg-emerald-500' : 'bg-rose-500'} animate-pulse`} />
                        Live Market Data • Last Updated: {data.last_updated}
                    </div>
                </div>

                {/* Grid Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <StatCard label="Previous Close" value={formatCurrency(data.previous_close)} />
                    <StatCard label="Open Price" value={formatCurrency(data.open)} />
                    <StatCard label="Day High" value={formatCurrency(data.day_high)} highlight />
                    <StatCard label="Day Low" value={formatCurrency(data.day_low)} />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-white dark:bg-[#13161b] p-6 rounded-2xl border border-slate-200 dark:border-white/5 flex items-center justify-between">
                        <div>
                            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">52 Week High</p>
                            <p className="text-xl font-bold text-emerald-500">{formatCurrency(data.year_high)}</p>
                        </div>
                        <div>
                            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1 text-right">52 Week Low</p>
                            <p className="text-xl font-bold text-rose-500 text-right">{formatCurrency(data.year_low)}</p>
                        </div>
                    </div>

                    <div className="bg-white dark:bg-[#13161b] p-6 rounded-2xl border border-slate-200 dark:border-white/5 grid grid-cols-2 gap-4">
                        <div>
                            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Market Cap</p>
                            <p className="text-xl font-bold">{formatIndianCompact(data.market_cap)}</p>
                        </div>
                        <div>
                            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Volume</p>
                            <p className="text-xl font-bold">{formatNumber(data.volume)}</p>
                        </div>
                    </div>
                </div>

                {/* Quarterly Results */}
                {
                    financials.length > 0 && (
                        <div className="bg-white dark:bg-[#13161b] rounded-3xl p-8 border border-slate-200 dark:border-white/5 shadow-xl">
                            <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-6">Quarterly Results</h3>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse">
                                    <thead>
                                        <tr className="border-b border-slate-100 dark:border-white/5">
                                            <th className="py-3 px-4 text-xs font-bold text-slate-500 uppercase">Period</th>
                                            <th className="py-3 px-4 text-xs font-bold text-slate-500 uppercase text-right">Revenue</th>
                                            <th className="py-3 px-4 text-xs font-bold text-slate-500 uppercase text-right">Net Income</th>
                                            <th className="py-3 px-4 text-xs font-bold text-slate-500 uppercase text-right">EBITDA</th>
                                            <th className="py-3 px-4 text-xs font-bold text-slate-500 uppercase text-right">EPS</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {financials.map((q, i) => (
                                            <tr key={i} className="border-b border-slate-50 dark:border-white/5 last:border-0 hover:bg-slate-50 dark:hover:bg-white/5 transition-colors">
                                                <td className="py-3 px-4 font-semibold text-slate-900 dark:text-white">{q.date}</td>
                                                <td className="py-3 px-4 text-right text-slate-700 dark:text-gray-300">{formatIndianCompact(q.revenue)}</td>
                                                <td className={`py-3 px-4 text-right font-bold ${q.net_income >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                                                    {formatIndianCompact(q.net_income)}
                                                </td>
                                                <td className="py-3 px-4 text-right text-slate-700 dark:text-gray-300">{formatIndianCompact(q.ebitda)}</td>
                                                <td className="py-3 px-4 text-right font-mono text-slate-700 dark:text-gray-300">₹{q.eps.toFixed(2)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )
                }
            </div >
        </div >
    );
};

const StatCard = ({ label, value, highlight }) => (
    <div className="bg-white dark:bg-[#13161b] p-5 rounded-2xl border border-slate-200 dark:border-white/5 hover:border-blue-500/30 transition-colors">
        <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">{label}</p>
        <p className={`text-lg font-bold ${highlight ? 'text-slate-900 dark:text-white' : 'text-slate-700 dark:text-gray-300'}`}>{value}</p>
    </div>
);

export default StockDetails;
