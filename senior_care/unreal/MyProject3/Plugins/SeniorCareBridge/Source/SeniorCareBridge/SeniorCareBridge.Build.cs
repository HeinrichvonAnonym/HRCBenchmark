// Copyright SeniorCare. Build rules for the SeniorCareBridge plugin module.

using System.IO;
using UnrealBuildTool;

public class SeniorCareBridge : ModuleRules
{
	public SeniorCareBridge(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;
		bEnableExceptions = true; // cppzmq's zmq.hpp throws on errors

		PublicIncludePaths.AddRange(new string[] { });
		PrivateIncludePaths.AddRange(new string[] { });

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"Slate",
			"SlateCore",
			"Json",
			"JsonUtilities",
			"UnrealEd",
			"EditorSubsystem",
		});

		// ---------------------------------------------------------------
		// Vendored libzmq (Linux x86_64 only for now)
		// ---------------------------------------------------------------
		string ThirdPartyPath = Path.GetFullPath(
			Path.Combine(ModuleDirectory, "..", "ThirdParty", "ZMQ"));

		if (Target.Platform == UnrealTargetPlatform.Linux)
		{
			string IncludeDir = Path.Combine(ThirdPartyPath, "Linux", "include");
			string LibDir = Path.Combine(ThirdPartyPath, "Linux", "lib");
			string SoFileVersioned = Path.Combine(LibDir, "libzmq.so.5");
			string SoFile = Path.Combine(LibDir, "libzmq.so");

			PublicSystemIncludePaths.Add(IncludeDir);

			// Link against the SONAME entry so the runtime loader looks
			// for libzmq.so.5 (which we ship next to the editor binary).
			PublicAdditionalLibraries.Add(SoFile);

			// Make sure the shared library is staged alongside the
			// plugin binaries when packaging, and is reachable at
			// editor-time runtime.
			RuntimeDependencies.Add(
				"$(BinaryOutputDir)/libzmq.so.5", SoFileVersioned);
			RuntimeDependencies.Add(
				"$(BinaryOutputDir)/libzmq.so", SoFile);
		}
	}
}
