export default function ImpactSummary() {
    return (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 text-center">
                <p className="text-3xl font-bold text-red-400">4</p>
                <p className="text-sm text-gray-400">Direct Impacts</p>
            </div>
            <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 text-center">
                <p className="text-3xl font-bold text-orange-400">12</p>
                <p className="text-sm text-gray-400">Indirect Impacts</p>
            </div>
            <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 text-center">
                <p className="text-3xl font-bold text-gray-500">2</p>
                <p className="text-sm text-gray-400">Unknown Impacts</p>
            </div>
            <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 text-center">
                <p className="text-3xl font-bold text-blue-400">3</p>
                <p className="text-sm text-gray-400">Revalidation Reqs</p>
            </div>
        </div>
    );
}