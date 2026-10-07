export default function EnvironmentBadge({ type }) {
    const colors = {
        development: 'text-green-400 border-green-800 bg-green-900/50',
        staging: 'text-yellow-400 border-yellow-800 bg-yellow-900/50',
        production: 'text-purple-400 border-purple-800 bg-purple-900/50'
    };
    return (
        <span className={`px-3 py-1 border rounded font-medium ${colors[type]}`}>{type.toUpperCase()}</span>
    );
}