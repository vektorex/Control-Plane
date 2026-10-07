export default function DecisionCard({ decision }) {
    return (
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="font-semibold text-white">{decision?.subject_type || 'Unknown'} - {decision?.overall_state || 'unknown'}</h3>
        </div>
    );
}