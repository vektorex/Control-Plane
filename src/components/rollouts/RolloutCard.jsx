export default function RolloutCard({ name, status, stage }) {
    const statusColors = {
        running: 'border-blue-500 bg-blue-900/20 text-blue-400',
        paused: 'border-yellow-500 bg-yellow-900/20 text-yellow-400',
        aborted: 'border-red-500 bg-red-900/20 text-red-400'
    };
    return (
        <div className="bg-gray-800 p-5 rounded-lg border border-gray-700 flex justify-between items-center hover:border-gray-500 transition-colors">
            <div>
                <h3 className="font-semibold text-white text-lg">{name}</h3>
                <p className="text-sm text-gray-400">Current Stage: {stage}</p>
            </div>
            <span className={`px-3 py-1 border rounded font-medium ${statusColors[status] || 'border-gray-500 text-gray-400'}`}>
                {status.toUpperCase()}
            </span>
        </div>
    );
}