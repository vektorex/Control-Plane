export default function RolloutGate({ type, status, details }) {
    const statusColors = {
        passed: 'text-green-400 border-green-800',
        failed: 'text-red-400 border-red-800',
        unknown: 'text-yellow-400 border-yellow-800'
    };
    return (
        <div className={`p-4 bg-gray-900 rounded border flex justify-between items-center ${statusColors[status]}`}>
            <div>
                <h4 className="font-bold">{type}</h4>
                <p className="text-sm opacity-80">{details}</p>
            </div>
            <span className="uppercase text-sm font-bold tracking-wider">{status}</span>
        </div>
    );
}