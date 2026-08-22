namespace QuantumGameplay.WorldComposer {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Math;

    // A single measured qubit chooses between two already-authored movement
    // candidates.  The input scores are classical and bounded; Q# does not
    // invent assets or replace the world generator.
    operation PickMovement(scoreA : Double, scoreB : Double) : Result {
        use q = Qubit();

        let safeA = MaxD(0.000001, scoreA);
        let safeB = MaxD(0.000001, scoreB);
        let theta = 2.0 * ArcTan2(Sqrt(safeB), Sqrt(safeA));

        Ry(theta, q);
        let measurement = M(q);
        ResetAll([q]);
        return measurement;
    }
}
