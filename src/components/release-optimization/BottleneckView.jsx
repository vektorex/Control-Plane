export default function BottleneckView() {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-red-500/30">
            <h3 className="font-bold text-white text-lg">Database Lock Bottleneck</h3>
            <p className="text-red-400 mt-1">Severity: HIGH</p>
            <p className="text-gray-400 text-sm mt-2">Dependency graph fan-in identifies REL-A (Database Migration) as blocking 12 downstream releases. Any delay to REL-A shifts the entire train.</p>
        </div>
    );
}